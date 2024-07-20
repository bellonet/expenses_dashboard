import streamlit as st
import pandas as pd
from constants import ColumnNames, Globals, Colors
import ai_queries
import utils_ai
import utils


def format_columns_all_dfs(dfs, container, ai_config, client):
    clean_dfs = []
    with container():
        for i, df in enumerate(dfs):
            df = rename_columns(df, ai_config, client, i)
            if all(col in df.columns for col in ColumnNames.initial_columns_as_list()
                   ) and len(df.columns) == len(set(df.columns)):
                df = format_df(df)
                clean_df = df[ColumnNames.as_list()]
                clean_dfs.append(clean_df)
        return clean_dfs


def rename_columns(df, ai_config, client, i):
    state_str = f'df{i}_columns'
    is_ran_ai_str = f'is_ran_ai_df{i}_column_names'
    if state_str not in st.session_state and is_ran_ai_str not in st.session_state:
        st.session_state[is_ran_ai_str] = True
        if not all(col in df.columns for col in ColumnNames.initial_columns_as_list()):
            df = ai_rename_columns(df, ai_config, client)
    df = add_missing_columns(df, ColumnNames.additional_columns_as_list())

    if all(c in df.columns for c in ColumnNames.initial_columns_as_list()):
        st.session_state[state_str] = df.columns
    else:
        manual_rename_columns(df, i)
    return df


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
        print("Date valid:", date_valid)
        amount_valid = check_column_format(df, utils.is_valid_float, new_columns.index(ColumnNames.AMOUNT))

        if date_valid and amount_valid:
            df.columns = new_columns
            utils.display_message(Colors.PRIMARY_COLOR, "Looks good!")

    else:
        utils.display_message('red', f"Please update the column names to include {ColumnNames.as_str()} "
                                     "using the dropdown lists provided.")

    st.dataframe(df.head())


def format_df(df):
    df.reset_index(drop=True, inplace=True)
    df = df[df[ColumnNames.AMOUNT].notna()]
    df = col_str_to_float(df)
    df = col_str_to_date(df)
    df = cols_to_str(df)
    return df


def get_allowed_columns(col, allowed_cols):
    allowed_cols = allowed_cols.copy()
    if col not in allowed_cols:
        allowed_cols.append(col)
    return allowed_cols


def cols_to_str(df):
    df[ColumnNames.CATEGORY] = df[ColumnNames.CATEGORY].fillna('').astype(str)
    df[ColumnNames.MERCHANT] = df[ColumnNames.MERCHANT].fillna('').astype(str)
    return df


def col_str_to_float(df, col=ColumnNames.AMOUNT):
    df[col] = df[col].apply(utils.str_to_float)
    return df


def col_str_to_date(df, col=ColumnNames.DATE):
    df[col] = df[col].apply(try_parsing_date)
    df[col] = df.apply(lambda row: find_alternative_date(row, df) if pd.isna(row[col]) else row[col], axis=1)
    df[col] = df[col].apply(lambda x: x.strftime(Globals.DATE_FORMAT) if not pd.isna(x) else x)
    df[col] = df[col].ffill()
    return df


def try_parsing_date(text):
    for fmt in Globals.INPUT_DATE_FORMATS:
        try:
            return pd.to_datetime(text, format=fmt, errors='coerce')
        except (ValueError, TypeError):
            continue
    return pd.NaT


def find_alternative_date(row, df):
    for column in df.columns:
        if column != ColumnNames.DATE:
            for fmt in Globals.INPUT_DATE_FORMATS:
                try:
                    temp_date = pd.to_datetime(row[column], format=fmt, errors='coerce')
                    if pd.notna(temp_date):
                        return temp_date
                except (ValueError, TypeError):
                    continue
    return pd.NaT


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


def concatenate_dfs(dfs):
    if len(dfs) > 0:
        df = pd.concat(dfs, ignore_index=True)
        st.write("Created a merged and formatted table.")
        return df
    else:
        st.error('No valid DataFrames to concatenate.')
