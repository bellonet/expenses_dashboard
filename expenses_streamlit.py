import streamlit as st
import pandas as pd
import json
import re
import numpy as np
import logging
import plotly.express as px
from types import SimpleNamespace


class ColumnNames:
    DATE = 'date'
    TEXT = 'text'
    COST = 'cost'

    @classmethod
    def as_list(cls):
        return [cls.DATE, cls.TEXT, cls.COST]

    @classmethod
    def as_set(cls):
        return {cls.DATE, cls.TEXT, cls.COST}

    @classmethod
    def as_str(cls):
        # Returns column names as a formatted string with single quotes and commas
        return ", ".join(f"'{name}'" for name in cls.as_list())


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info("Logging test")
    return logger


def str_to_float(value):
    if re.match(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$', value):
        # German format (e.g., -1.000,23 or 1.000,23)
        value = value.replace('.', '').replace(',', '.')
    elif re.match(r'^-?\d{1,3}(?:,\d{3})*\.\d{2}$', value):
        # English format (e.g., -1,000.23 or 1,000.23)
        value = value.replace(',', '')
    elif re.match(r'^-?\d+(\,\d{2})$', value):
        # German simple format (e.g., -1000,23 or 1000,23)
        value = value.replace(',', '.')
    elif re.match(r'^-?\d+(\.\d{2})$', value):
        # English simple format (e.g., -1000.23 or 1000.23)
        value = value
    return float(value)


def convert_dates(df, date_col=ColumnNames.DATE):
    df[date_col] = pd.to_datetime(df[date_col], 
                                format='%d.%m.%Y', 
                                errors='coerce')
    df[date_col].fillna(method='ffill', inplace=True)    
    return df
   

def reorganize_df(df):
    df.rename(columns={'Buchungstag': ColumnNames.DATE,
                        'Umsatz in EUR': ColumnNames.COST, 
                        'Buchungstext': ColumnNames.TEXT, 
                        'Vorgang':'type'}, inplace=True)
    df = df[df['cost'].notna()]
    df = df.drop(columns=['Umsatztag', 'Referenz', 'Wertstellung (Valuta)'])
    df = df[df['type'] != 'Visa-Kartenabrechnung']
    df = df[~df['type'].str.contains('Guthaben', case=False, na=False)]
    str_col_to_float(df)
    df = convert_dates(df)
    df['category'] = ''
    return df 


def read_categories(json_path='categories.json'):
    with open(json_path, 'r') as json_file:
        categories_dict = json.load(json_file)
    return categories_dict


def read_strs_to_del(json_path='delete_list.json'):
    with open(json_path, 'r') as json_file:
        to_del_list = json.load(json_file)
    return to_del_list


def add_categories(df, categories_dict):
    for category_name, keywords in categories_dict.items():
        pattern = '|'.join(re.escape(keyword) for keyword in keywords)
        df['category'] = np.where(df['category'].str.strip() == '', 
                                  np.where(df['name'].str.contains(pattern, case=False, na=False), 
                                           category_name, df['category']), df['category'])


def delete_rows(df, to_del_list):
    pattern = '|'.join(re.escape(item) for item in to_del_list)
    return df[~df['name'].str.contains(pattern, case=False, na=False)]


def set_st():
    st.set_page_config(layout="wide")
    st.title('Expenses Analyzer - Comdirect')


def upload_csvs_to_dfs():
    csv_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type=['csv'])
    all_dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            all_dfs.append(df)
            logger.info(f"Successfully processed {f.name}")
        except Exception as e:
            st.error(f"Error processing {f.name}: {e}")
            logger.error(f"Error processing {f.name}: {e}")
    return all_dfs


def load_column_mappings(file_path="column_mappings.json"):
    with open(file_path, "r") as file:
        return json.load(file)


def auto_rename_columns(df):
    mappings = load_column_mappings()
    new_columns = {col: col for col in df.columns}  # Initialize with the original column names

    for standard_name, possible_names in mappings.items():
        for possible_name in possible_names:
            if possible_name in df.columns:
                new_columns[possible_name] = standard_name
                break

    df.rename(columns=new_columns, inplace=True)
    return df


def rename_columns_all_dfs(dfs, bank_name):
    for i, df in enumerate(dfs):
        dfs[i] = auto_rename_columns(df, bank_name)
        rename_columns(dfs[i], i)
    return dfs


def display_message(color, message):
    st.markdown(f"<span style='color: {color};'>{message}</span>", unsafe_allow_html=True)


def get_allowed_columns(col, allowed_cols):
    allowed_cols = allowed_cols.copy()
    if col not in allowed_cols:
        allowed_cols.append(col)
    return allowed_cols


def is_valid_date(date_str):
    try:
        pd.to_datetime(date_str, dayfirst=True)
        return True
    except ValueError:
        display_message('red', f"The 'date' column is not in a valid date format.")
        return False


def is_valid_float(float_str):
    try:
        # Check for German format (e.g., -1.000,23 or 1.000,23)
        if re.match(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$', float_str):
            return True
        # Check for English format (e.g., -1,000.23 or 1,000.23)
        elif re.match(r'^-?\d{1,3}(?:,\d{3})*\.\d{2}$', float_str):
            return True
        # Check for plain formats (e.g., -1000.23 or 1000.23 or -1000,23 or 1000,23)
        elif re.match(r'^-?\d+(\.\d{2})$', float_str) or re.match(r'^-?\d+(\,\d{2})$', float_str):
            return True
        display_message('red', f"The 'cost' column is not in a valid float format.")
        return False
    except ValueError:
        display_message('red', f"The 'cost' column is not in a valid float format.")
        return False


def check_column_format(df, is_valid_func, col_idx):
    first_item = df.iloc[0, col_idx]
    if not is_valid_func(first_item):
        return False
    return True


def rename_columns(df, idx):
    with st.container():
        cols = st.columns(len(df.columns))
        new_columns = []

        for i, col in enumerate(df.columns):
            allowed_cols = get_allowed_columns(col, ColumnNames.as_list())
            
            with cols[i]:
                new_col = st.selectbox(f"Rename '{col}'", options=allowed_cols,
                                       index=allowed_cols.index(col), key=f"{idx}_{col}")
                new_columns.append(new_col)

        if len(set(new_columns)) != len(new_columns):
            display_message('red', "Multiple columns have the same name. Please ensure all column names are unique.")
        elif all(name in new_columns for name in ColumnNames.as_list()):

            date_valid = check_column_format(df, 
                                            is_valid_date, 
                                            new_columns.index(ColumnNames.DATE))
            cost_valid = check_column_format(df, 
                                            is_valid_float, 
                                            new_columns.index(ColumnNames.COST))

            if date_valid and cost_valid:
                df.columns = new_columns
                display_message('green', "Looks good!")

        else:
            display_message('red', f"Please update the column names to include {ColumnNames.as_str()} using the dropdown lists provided.")

        st.dataframe(df.head())


def rename_columns_all_dfs(dfs):
    clean_dfs = []  # Initialize the list to store cleaned DataFrames
    for i, df in enumerate(dfs):
        df = auto_rename_columns(df)  # Automatically rename columns
        rename_columns(df, i)  # Allow user to rename columns if needed
        # Check if DataFrame has the required columns and unique names
        if all(col in df.columns for col in ColumnNames.as_set()) and len(df.columns) == len(set(df.columns)):
            clean_df = df[ColumnNames.as_list()]
            clean_dfs.append(clean_df)
    return clean_dfs

    

def concatenate_dfs(dfs):
    if len(dfs) > 0:
        final_df = pd.concat(dfs, ignore_index=True)
        st.dataframe(final_df)
        logger.info("Successfully concatenated all dataframes")
        return final_df
    else:
        st.error('No valid DataFrames to concatenate.')


logger = set_logger()

categories_dict = read_categories()
str_to_del = read_strs_to_del()

set_st()
all_dfs = upload_csvs_to_dfs()
if all_dfs:
    valid_dfs = rename_columns_all_dfs(all_dfs)
    if len(valid_dfs) == len(all_dfs):
        df = concatenate_dfs(valid_dfs)
        st.markdown("<span style='color: green;'>Done</span>", unsafe_allow_html=True)


        # df = reorganize_df(df)
        # add_categories(df, categories_dict)
        # df = delete_rows(df, str_to_del)
        # #st.write("## Concatenated DataFrame")

        # if not df.empty:
        #     min_date = df['date'].min().date()  # Convert Pandas Timestamp to Python date
        #     max_date = df['date'].max().date()  # Convert Pandas Timestamp to Python date
            
        #     # Create a date range selector
        #     date_range = st.sidebar.date_input("Select date range:", [min_date, max_date])
            
        #     if len(date_range) == 2:
        #         start_date, end_date = date_range
        #         # Convert Python date to Pandas Timestamp for comparison
        #         start_date = pd.Timestamp(start_date)
        #         end_date = pd.Timestamp(end_date)
                
        #         # Filter the DataFrame based on the selected date range
        #         filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        #     else:
        #         filtered_df = df 


        #     st.dataframe(filtered_df.head(10))
        #     #st.dataframe(df[df.category=='sports_equipment'].head(30))
            
        #     df_grouped = filtered_df.groupby('category')['cost'].sum().reset_index()
        #     df_grouped['cost'] = df_grouped['cost'].abs()  

        #     # Create a pie chart using the grouped and absolute values
        #     if not df_grouped.empty and 'cost' in df_grouped.columns and 'category' in df_grouped.columns:
        #         fig = px.pie(
        #             df_grouped, 
        #             values='cost', 
        #             names='category', 
        #             title='Expenses by Category',
        #             width=1000,  # Increase the width
        #             height=1000,  # Increase the height
        #             hole=0.4  # Make it a donut chart for better space utilization
        #         )
                
        #         # Update the layout to show values and percentages
        #         fig.update_traces(textinfo='label+percent', insidetextorientation='radial', 
        #                           texttemplate='%{label}<br>%{value:.2f}€  -  %{percent}')
        #         # fig.update_traces(textinfo='label+percent', insidetextorientation='radial', 
        #         #       texttemplate='%{label}<br>%{value:.2f}€<br>(%{percent})')

        #         fig.update_layout(
        #             legend_title="Categories",
        #             legend=dict(
        #                 orientation="h",
        #                 yanchor="bottom",
        #                 y=-0.25,  # Adjust as needed for optimal positioning
        #                 xanchor="center",
        #                 x=0.5
        #             )
        #         )
                
        #         st.plotly_chart(fig)
        #     else:
        #         st.write("No valid data to plot.")

        #     if not filtered_df.empty:
        #         filtered_df['month'] = filtered_df['date'].dt.to_period('M').astype(str)
        #         monthly_expenses = filtered_df.groupby(['month', 'category'])['cost'].sum().abs().reset_index()

        #         # Create a bar chart
        #         fig = px.bar(
        #             monthly_expenses,
        #             x='month',
        #             y='cost',
        #             color='category',
        #             title='Monthly Expenses by Category',
        #             labels={'month': 'Month', 'cost': 'Expenses (€)'},
        #             height=600,
        #             text='cost'
        #         )
                
        #         # Improve the layout
        #         fig.update_layout(
        #             xaxis_title='Month',
        #             yaxis_title='Total Expenses',
        #             barmode='stack',
        #             xaxis={'type': 'category'},  # This ensures the x-axis treats months as discrete categories
        #             legend_title='Categories'
        #         )
                
        #         # Display the bar chart in Streamlit
        #         st.plotly_chart(fig)
        #     else:
        #         st.write("No data available for the selected date range to plot.")
