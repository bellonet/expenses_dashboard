import re
import pandas as pd
from constants import ColumnNames
import streamlit as st


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


def col_str_to_float(df, col=ColumnNames.COST):
    df[col] = df[col].apply(str_to_float)
    return df


def col_str_to_date(df, col=ColumnNames.DATE):
    df[col] = pd.to_datetime(df[col], format='%d.%m.%Y', errors='coerce')
    df[col] = df[col].dt.strftime('%d.%m.%Y')
    df[col].fillna(method='ffill', inplace=True)
    return df


def get_date_col_as_datetime(df, col=ColumnNames.DATE, date_format='%d.%m.%Y'):
    return pd.to_datetime(df[col], format=date_format, errors='coerce')


def format_df(df):
    df.reset_index(drop=True, inplace=True)
    df = df[df[ColumnNames.COST].notna()]
    df = col_str_to_float(df)
    df = col_str_to_date(df)
    return df


def display_message(color, message):
    st.markdown(f"<span style='color: {color};'>{message}</span>", unsafe_allow_html=True)


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
