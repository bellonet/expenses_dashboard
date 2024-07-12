import pandas as pd
import streamlit as st
import numpy as np
import re
from constants import ColumnNames, Colors, Globals
import utils
import utils_ai
import ai_queries


def col_str_to_float(df, col=ColumnNames.AMOUNT):
    df[col] = df[col].apply(utils.str_to_float)
    return df


def find_alternative_date(row, df):
    for column in df.columns:
        temp_date = pd.to_datetime(row[column], format=Globals.DATE_FORMAT, errors='coerce')
        if pd.notna(temp_date):
            return temp_date
    return None


def col_str_to_date(df, col=ColumnNames.DATE):
    df[col] = pd.to_datetime(df[col], format=Globals.DATE_FORMAT, errors='coerce')
    df[col] = df.apply(lambda row: find_alternative_date(row, df) if pd.isna(row[col]) else row[col], axis=1)
    df[col] = df[col].apply(lambda x: x.strftime(Globals.DATE_FORMAT) if not pd.isna(x) else x)
    df[col] = df[col].ffill()
    return df


def get_date_col_as_datetime(df, col=ColumnNames.DATE, date_format=Globals.DATE_FORMAT):
    return pd.to_datetime(df[col], format=date_format, errors='coerce')


def format_df(df):
    df.reset_index(drop=True, inplace=True)
    df = df[df[ColumnNames.AMOUNT].notna()]
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


def manual_rename_columns(df, idx):

    cols = st.columns(len(df.columns))
    new_columns = []

    for i, col in enumerate(df.columns):
        if col == ColumnNames.MERCHANT:
            allowed_cols = [ColumnNames.MERCHANT]
        elif col == ColumnNames.CATEGORY:
            allowed_cols = [ColumnNames.CATEGORY]
        else:
            allowed_cols = [c for c in get_allowed_columns(col, ColumnNames.initial_columns_as_list())]

        with cols[i]:
            new_col = st.selectbox(f"Rename '{col}'", options=allowed_cols,
                                   index=allowed_cols.index(col), key=f"{idx}_{col}")
            new_columns.append(new_col)

    if len(set(new_columns)) != len(new_columns):
        utils.display_message('red', "Multiple columns have the same name. Please ensure all column names are unique.")
    elif all(name in new_columns for name in ColumnNames.as_list()):

        date_valid = check_column_format(df, utils.is_valid_date, new_columns.index(ColumnNames.DATE))
        amount_valid = check_column_format(df, utils.is_valid_float, new_columns.index(ColumnNames.AMOUNT))

        if date_valid and amount_valid:
            df.columns = new_columns
            utils.display_message(Colors.PRIMARY_COLOR, "Looks good!")

    else:
        utils.display_message('red', f"Please update the column names to include {ColumnNames.as_str()} "
                                     "using the dropdown lists provided.")

    st.dataframe(df.head())


def ai_rename_columns(df, ai_config, client):
    column_names = df.columns
    query = ai_queries.get_column_names_query(column_names)
    column_name_dict_as_str = utils_ai.query_ai(query, ai_config, client)
    column_names_dict = utils.get_dict_from_string(column_name_dict_as_str, flip=True)
    df = df.rename(columns=column_names_dict)
    return df


def add_missing_columns(df, new_columns):
    for col in new_columns:
        if col not in df.columns:
            df[col] = ''
    return df


def rename_columns(df, ai_config, client, i):
    df = ai_rename_columns(df, ai_config, client)
    df = add_missing_columns(df, ColumnNames.additional_columns_as_list())
    if not all(col in df.columns for col in ColumnNames.initial_columns_as_list()):
        manual_rename_columns(df, i)
    return df


def format_columns_all_dfs(dfs, container, ai_config, client):
    clean_dfs = []
    with (container()):
        for i, df in enumerate(dfs):
            df = rename_columns(df, ai_config, client, i)
            if all(col in df.columns for col in ColumnNames.initial_columns_as_list()
                   ) and len(df.columns) == len(set(df.columns)):
                df = format_df(df)
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

    if 'is_uploaded' not in st.session_state:
        set_upload_csv_state()

    if not st.session_state.is_uploaded:
        csv_files = st.file_uploader("Upload CSV files - bank statements, credit card statements, etc.",
                                     accept_multiple_files=True, type=['csv'])

        if csv_files:
            for f in csv_files:
                try:
                    df = pd.read_csv(f)
                    st.session_state.all_dfs.append(df)
                    st.session_state.uploaded_files.append(f.name)
                except Exception as e:
                    st.error(f"Error processing {f.name}: {e}")
            st.session_state.is_uploaded = True
            st.rerun()

    else:
        st.write(f"Uploaded files: {' '.join(st.session_state.uploaded_files)}")

        if st.button("Start Over"):
            set_upload_csv_state()
            st.experimental_rerun()

    return st.session_state.all_dfs


def set_upload_csv_state():
    st.session_state.is_uploaded = False
    st.session_state.all_dfs = []
    st.session_state.uploaded_files = []


def concatenate_dfs(dfs):
    if len(dfs) > 0:
        df = pd.concat(dfs, ignore_index=True)
        st.write("Created a merged and formatted table.")
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
    monthly_expenses = df.groupby(['month', ColumnNames.CATEGORY])[ColumnNames.AMOUNT].sum().reset_index()
    category_order = df_grouped.sort_values(by=ColumnNames.AMOUNT, ascending=False)[ColumnNames.CATEGORY].tolist()
    monthly_expenses[ColumnNames.CATEGORY] = pd.Categorical(monthly_expenses[ColumnNames.CATEGORY],
                                                            categories=category_order,
                                                            ordered=True)
    return monthly_expenses


def add_merchants(df, ai_config, client):

    if not st.session_state.is_ran_merchant:
        for i in range(4):
            mask = (df[ColumnNames.MERCHANT].isna() |
                    (df[ColumnNames.MERCHANT] == '') |
                    (df[ColumnNames.MERCHANT] == ','))
            texts_list = df.loc[mask, ColumnNames.TEXT].tolist()
            if texts_list:
                df.loc[mask, ColumnNames.MERCHANT] = utils.ai_get_merchants_from_text(texts_list, ai_config, client)

            df[ColumnNames.MERCHANT] = utils.standardize_merchant_names(df[ColumnNames.MERCHANT].tolist())

        df[ColumnNames.MERCHANT] = utils.ai_standardize_merchant_names(df[ColumnNames.MERCHANT].tolist(),
                                                                       ai_config, client)

        st.session_state.is_ran_merchant = True
        st.session_state.current_df = df

    df = st.data_editor(df)
    return df
