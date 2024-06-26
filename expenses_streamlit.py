import streamlit as st
import pandas as pd
import json
import re
import numpy as np
import logging
import plotly.express as px


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info("Logging test")
    return logger


def str_col_to_float(df):
    df['cost'] = df['cost'].str.replace('.', '', regex=False)
    df['cost'] = df['cost'].str.replace(',', '.')
    df['cost'] = df['cost'].astype(float)
   

def reorganize_df(df):
    df.rename(columns={'Umsatz in EUR': 'cost', 'Buchungstext': 'name', 'Vorgang':'type'}, inplace=True)
    df = df[df['cost'].notna()]
    df = df.drop(columns=['Umsatztag', 'Referenz', 'Wertstellung (Valuta)'])
    df = df[df['type'] != 'Visa-Kartenabrechnung']
    df = df[~df['type'].str.contains('Guthaben', case=False, na=False)]
    str_col_to_float(df)
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


logger = set_logger()
st.title('Expenses Analyzer - Comdirect')

categories_dict = read_categories()
str_to_del = read_strs_to_del()

uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type=['csv'])

if uploaded_files:
    all_dfs = []
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_csv(uploaded_file)
            #df = clean_df(df)
            #st.write(f"## {uploaded_file.name}")
            #st.dataframe(df.head())
            all_dfs.append(df)
            logger.info(f"Successfully processed {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
            logger.error(f"Error processing {uploaded_file.name}: {e}")

    if all_dfs:
        df = pd.concat(all_dfs, ignore_index=True)
        logger.info("Successfully concatenated all dataframes")
        df = reorganize_df(df)
        add_categories(df, categories_dict)
        df = delete_rows(df, str_to_del)
        #st.write("## Concatenated DataFrame")
        #st.dataframe(df.head(100))
        #st.dataframe(df[df.category=='sports_equipment'].head(30))
        
        df_grouped = df.groupby('category')['cost'].sum().reset_index()
        
        # Convert the summed values to their absolute values
        df_grouped['cost'] = df_grouped['cost'].abs()
        
        # if not df_grouped.empty and 'cost' in df_grouped.columns and 'category' in df_grouped.columns:
        #     fig = px.pie(df_grouped, values='cost', names='category', title='Expenses by Category')
        #     st.plotly_chart(fig)
        # else:
        #     st.write("No valid data to plot.")

        # Create a pie chart using the grouped and absolute values

        # Create a pie chart using the grouped and absolute values
        if not df_grouped.empty and 'cost' in df_grouped.columns and 'category' in df_grouped.columns:
            fig = px.pie(
                df_grouped, 
                values='cost', 
                names='category', 
                title='Expenses by Category',
                width=800,  # Increase the width
                height=600,  # Increase the height
                hole=0.4  # Make it a donut chart for better space utilization
            )
            
            # Update the layout to show values and percentages
            fig.update_traces(textinfo='label+percent', insidetextorientation='radial', 
                              texttemplate='%{label}<br>%{value:.2f}€<br>(%{percent})')
            fig.update_layout(
                showlegend=True,
                legend_title="Categories"
            )
            
            st.plotly_chart(fig)
        else:
            st.write("No valid data to plot.")
