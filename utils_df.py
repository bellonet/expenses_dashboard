import pandas as pd
import streamlit as st
import numpy as np
import re
from constants import ColumnNames, Colors
import utils


def col_str_to_float(df, col=ColumnNames.COST):
    df[col] = df[col].apply(utils.str_to_float)
    return df


def col_str_to_date(df, col=ColumnNames.DATE):
    df[col] = pd.to_datetime(df[col], format='%d.%m.%Y', errors='coerce')
    df[col] = df[col].dt.strftime('%d.%m.%Y')
    df[col] = df[col].ffill()
    return df


def get_date_col_as_datetime(df, col=ColumnNames.DATE, date_format='%d.%m.%Y'):
    return pd.to_datetime(df[col], format=date_format, errors='coerce')


def format_df(df):
    df.reset_index(drop=True, inplace=True)
    df = df[df[ColumnNames.COST].notna()]
    df = col_str_to_float(df)
    df = col_str_to_date(df)
    return df


def check_column_format(df, is_valid_func, col_idx):
    first_item = df.iloc[0, col_idx]
    if not is_valid_func(first_item):
        return False
    return True


def auto_rename_columns(df):
    mappings = utils.load_json(file_path="json/column_mappings.json")
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
        df[ColumnNames.CATEGORY] = ''

    cols = st.columns(len(df.columns))
    new_columns = []

    for i, col in enumerate(df.columns):
        if col == ColumnNames.CATEGORY:
            allowed_cols = [ColumnNames.CATEGORY]
        else:
            allowed_cols = [c for c in get_allowed_columns(col, ColumnNames.as_list()) if c != ColumnNames.CATEGORY]

        with cols[i]:
            new_col = st.selectbox(f"Rename '{col}'", options=allowed_cols,
                                   index=allowed_cols.index(col), key=f"{idx}_{col}")
            new_columns.append(new_col)

    if len(set(new_columns)) != len(new_columns):
        utils.display_message('red', "Multiple columns have the same name. Please ensure all column names are unique.")
    elif all(name in new_columns for name in ColumnNames.as_list()):

        date_valid = check_column_format(df, utils.is_valid_date, new_columns.index(ColumnNames.DATE))
        cost_valid = check_column_format(df, utils.is_valid_float, new_columns.index(ColumnNames.COST))

        if date_valid and cost_valid:
            df.columns = new_columns
            utils.display_message(Colors.PRIMARY_COLOR, "Looks good!")

    else:
        utils.display_message('red', f"Please update the column names to include {ColumnNames.as_str()} "
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


def get_min_max_date(df):
    min_date = get_date_col_as_datetime(df).min().date()
    max_date = get_date_col_as_datetime(df).max().date()
    return min_date, max_date


def filter_df_by_date_range(df):

    min_date, max_date = get_min_max_date(df)

    date_range = st.sidebar.date_input("Select date range:", [min_date, max_date])

    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)

        return df[(get_date_col_as_datetime(df) >= start_date) & (get_date_col_as_datetime(df) <= end_date)]
    else:
        return df


def apply_date_filter(df):
    return filter_df_by_date_range(df)


def apply_category_filter(df, selected_categories):
    df = df[df['category'].apply(lambda x: x in selected_categories and selected_categories[x])]
    return df


def add_categories_to_df(df, categories_dict):
    for category_name, keywords in categories_dict.items():
        pattern = '|'.join(re.escape(keyword) for keyword in keywords)
        df['category'] = np.where(df['category'].str.strip() == '',
                                  np.where(df[ColumnNames.TEXT].str.contains(pattern, case=False, na=False),
                                           category_name, df['category']), df['category'])


def delete_rows(df, to_del_list):
    pattern = '|'.join(re.escape(item) for item in to_del_list)
    return df[~df[ColumnNames.TEXT].str.contains(pattern, case=False, na=False)]


def upload_csvs_to_dfs():
    csv_files = st.file_uploader("Upload CSV files - bank statements, credit card statements, etc.",
                                 accept_multiple_files=True, type=['csv'])
    all_dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            all_dfs.append(df)
        except Exception as e:
            st.error(f"Error processing {f.name}: {e}")
    return all_dfs


def concatenate_dfs(dfs):
    if len(dfs) > 0:
        df = pd.concat(dfs, ignore_index=True)
        df = format_df(df)
        utils.display_message(Colors.PRIMARY_COLOR, "Created a formated and merged table!")
        return df
    else:
        st.error('No valid DataFrames to concatenate.')


def save_df_to_csv(df):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download current CSV",
                       data=csv,
                       file_name='expenses_formated.csv',
                       mime='text/csv')
    st.warning('''Save your work by downloading the CSV  
                Make sure you don't select unwanted filters!''')


def get_monthly_expense_df(df, df_grouped):
    df['month'] = get_date_col_as_datetime(df).dt.to_period('M').astype(str)
    monthly_expenses = df.groupby(['month', ColumnNames.CATEGORY])[ColumnNames.COST].sum().reset_index()
    category_order = df_grouped.sort_values(by=ColumnNames.COST, ascending=False)[ColumnNames.CATEGORY].tolist()
    monthly_expenses[ColumnNames.CATEGORY] = pd.Categorical(monthly_expenses[ColumnNames.CATEGORY],
                                                            categories=category_order,
                                                            ordered=True)
    return monthly_expenses


# create a function that makes a merchant column in the dataframe:
def make_merchant_column(df, ai_config, client):
    df['merchant'] = utils.get_merchants_from_text_chatgpt(df[ColumnNames.TEXT].tolist(), ai_config, client)
    return df
