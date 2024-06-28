import streamlit as st
import pandas as pd
import json
import re
import numpy as np
import logging
import utils
from constants import ColumnNames
from plots import plot_pie_chart, plot_bar_chart


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info("Logging test")
    return logger


def read_categories(json_path='json/categories.json'):
    with open(json_path, 'r') as json_file:
        categories_dict = json.load(json_file)
    return categories_dict


def read_strs_to_del(json_path='json/delete_list.json'):
    with open(json_path, 'r') as json_file:
        to_del_list = json.load(json_file)
    return to_del_list


def add_categories(df, categories_dict):
    if 'category' not in df.columns:
        df['category'] = ''
    for category_name, keywords in categories_dict.items():
        pattern = '|'.join(re.escape(keyword) for keyword in keywords)
        df['category'] = np.where(df['category'].str.strip() == '',
                                  np.where(df[ColumnNames.TEXT].str.contains(pattern, case=False, na=False),
                                           category_name, df['category']), df['category'])


def delete_rows(df, to_del_list):
    pattern = '|'.join(re.escape(item) for item in to_del_list)
    return df[~df[ColumnNames.TEXT].str.contains(pattern, case=False, na=False)]


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


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def auto_rename_columns(df):
    mappings = load_json(file_path="json/column_mappings.json")
    new_columns = {col: col for col in df.columns}  # Initialize with the original column names

    for standard_name, possible_names in mappings.items():
        for possible_name in possible_names:
            if possible_name in df.columns:
                new_columns[possible_name] = standard_name
                break

    df.rename(columns=new_columns, inplace=True)
    return df


def get_allowed_columns(col, allowed_cols):
    allowed_cols = allowed_cols.copy()
    if col not in allowed_cols:
        allowed_cols.append(col)
    return allowed_cols


def rename_columns(df, idx):

    if ColumnNames.CATEGORY not in df.columns:
        df[ColumnNames.CATEGORY] = ''  # Initialize with None or suitable default

    cols = st.columns(len(df.columns))
    new_columns = []

    for i, col in enumerate(df.columns):
        if col == ColumnNames.CATEGORY:
            allowed_cols = [ColumnNames.CATEGORY]  # Only CATEGORY allowed for its own column
        else:
            allowed_cols = [c for c in get_allowed_columns(col, ColumnNames.as_list()) if c != ColumnNames.CATEGORY]

        with cols[i]:
            new_col = st.selectbox(f"Rename '{col}'", options=allowed_cols,
                                   index=allowed_cols.index(col), key=f"{idx}_{col}")
            new_columns.append(new_col)

    if len(set(new_columns)) != len(new_columns):
        utils.display_message('red',
                              "Multiple columns have the same name. Please ensure all column names are unique.")
    elif all(name in new_columns for name in ColumnNames.as_list()):

        date_valid = utils.check_column_format(df, utils.is_valid_date, new_columns.index(ColumnNames.DATE))
        cost_valid = utils.check_column_format(df, utils.is_valid_float, new_columns.index(ColumnNames.COST))

        if date_valid and cost_valid:
            df.columns = new_columns
            utils.display_message('green', "Looks good!")

    else:
        utils.display_message('red',
                              f"Please update the column names to include {ColumnNames.as_str()} "
                              "using the dropdown lists provided.")

    st.dataframe(df.head())


def rename_columns_all_dfs(dfs, container):
    clean_dfs = []
    with container():
        for i, df in enumerate(dfs):
            df = auto_rename_columns(df)
            rename_columns(df, i)
            if all(col in df.columns for col in ColumnNames.as_set()) and len(df.columns) == len(set(df.columns)):
                clean_df = df[ColumnNames.as_list()]
                clean_dfs.append(clean_df)
        return clean_dfs


def concatenate_dfs(dfs):
    utils.display_message('green', "Formated and merged table!")
    if len(dfs) > 0:
        df = pd.concat(dfs, ignore_index=True)
        df = utils.format_df(df)
        logger.info("Successfully concatenated all dataframes")
        return df
    else:
        st.error('No valid DataFrames to concatenate.')


def save_df_to_csv(df):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download concatenated data as CSV",
                       data=csv,
                       file_name='expenses_formated.csv',
                       mime='text/csv')
    st.warning('Make sure to save your work by downloading the formated and concatenated CSV.')


def filter_df_by_date_range(df, date_col):
    min_date = utils.get_date_col_as_datetime(df).min().date()
    max_date = utils.get_date_col_as_datetime(df).max().date()

    date_range = st.sidebar.date_input("Select date range:", [min_date, max_date])

    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)

        return df[(utils.get_date_col_as_datetime(df) >= start_date) & (utils.get_date_col_as_datetime(df) <= end_date)]
    else:
        return df


logger = set_logger()

categories_dict = read_categories()
to_del_substr_l = read_strs_to_del()

set_st()
all_dfs = upload_csvs_to_dfs()
placeholder = st.empty()
if all_dfs:
    valid_dfs = rename_columns_all_dfs(all_dfs, placeholder.container)
    if len(valid_dfs) == len(all_dfs):
        placeholder.empty()
        df = concatenate_dfs(valid_dfs)

        add_categories(df, categories_dict)
        df = delete_rows(df, to_del_substr_l)
        st.dataframe(df)
        save_df_to_csv(df)
        if not df.empty:
            filtered_df = filter_df_by_date_range(df, utils.get_date_col_as_datetime(df))
            st.dataframe(filtered_df.head(10))

            df_grouped = filtered_df.groupby('category')[ColumnNames.COST].sum().reset_index()
            df_grouped[ColumnNames.COST] = df_grouped[ColumnNames.COST].abs()

            if not df_grouped.empty:
                plot_pie_chart(df_grouped)
            else:
                st.write("No valid data to plot.")

            if not filtered_df.empty:
                filtered_df['month'] = utils.get_date_col_as_datetime(filtered_df).dt.to_period('M').astype(str)
                monthly_expenses = filtered_df.groupby(['month', 'category'])[
                    ColumnNames.COST].sum().abs().reset_index()
                plot_bar_chart(monthly_expenses)
            else:
                st.write("No data available for the selected date range to plot.")
