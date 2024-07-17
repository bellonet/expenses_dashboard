import re
import pandas as pd
import numpy as np
import streamlit as st
import json
from collections import OrderedDict
import ast
from io import StringIO
import utils_ai
import ai_queries
from constants import Globals, ColumnNames


def str_to_float(value):
    if isinstance(value, float):
        return value
    if re.match(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$', value):
        # German format (e.g., -1.000,23 or 1.000,23)
        value = value.replace('.', '').replace(',', '.')
    elif re.match(r'^-?\d{1,3}(?:,\d{3})*\.\d{2}$', value):
        # English format (e.g., -1,000.23 or 1,000.23)
        value = value.replace(',', '')
    elif re.match(r'^-?\d+(,\d{2})$', value):
        # German simple format (e.g., -1000,23 or 1000,23)
        value = value.replace(',', '.')
    elif re.match(r'^-?\d+(\.\d{2})$', value):
        # English simple format (e.g., -1000.23 or 1000.23)
        value = value
    return float(value)


def get_date_col_as_datetime(df, col=ColumnNames.DATE, date_format=Globals.DATE_FORMAT):
    return pd.to_datetime(df[col], format=date_format, errors='coerce')


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
        if isinstance(float_str, float):
            return True
        # Check for German format (e.g., -1.000,23 or 1.000,23)
        if re.match(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$', float_str):
            return True
        # Check for English format (e.g., -1,000.23 or 1,000.23)
        elif re.match(r'^-?\d{1,3}(?:,\d{3})*\.\d{2}$', float_str):
            return True
        # Check for plain formats (e.g., -1000.23 or 1000.23 or -1000,23 or 1000,23)
        elif re.match(r'^-?\d+(\.\d{2})$', float_str) or re.match(r'^-?\d+(,\d{2})$', float_str):
            return True
        display_message('red', f"The 'amount' column is not in a valid float format.")
        return False
    except ValueError:
        display_message('red', f"The 'amount' column is not in a valid float format.")
        return False


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def read_categories(json_path='json/categories.json'):
    with open(json_path, 'r') as json_file:
        categories_dict = json.load(json_file)
    return OrderedDict(sorted(categories_dict.items()))


def add_new_category(categories_dict, new_category):
    if new_category and new_category not in categories_dict:
        categories_dict[new_category] = new_category  # or an appropriate value
        sorted_categories = OrderedDict(sorted(categories_dict.items()))
        return sorted_categories
    return categories_dict


def add_categories_to_session_state(df):
    if not df.empty:
        if not df[ColumnNames.CATEGORY].eq('').all():
            st.session_state.categories = df[ColumnNames.CATEGORY].unique()
        elif 'categories' not in st.session_state:
            placeholder = st.empty()
            with placeholder.container():
                categories_temp = ''
                categories_temp = st.text_input("Please enter your categories here, separated by a comma:",
                                                placeholder="groceries, rent/bills, restaurants, sport...")

                if categories_temp != '':
                    st.write(f"Categories: {categories_temp}")
                    if st.button("Categories look good (for now)"):
                        st.session_state.categories = categories_temp.split(',')
                        placeholder.empty()


def read_strs_to_del(json_path='json/delete_list.json'):
    with open(json_path, 'r') as json_file:
        to_del_list = json.load(json_file)
    return to_del_list


def invert_amounts(df, amount_column):
    """Invert the sign of the amount column in the DataFrame."""
    df[amount_column] = -df[amount_column]
    return df


def get_list_chunks(full_list, chunk_size):
    chunks = [full_list[i:i + chunk_size] for i in range(0, len(full_list), chunk_size)]
    return chunks


def get_dict_from_string(string, flip=False):
    start = string.find('{')
    end = string.find('}') + 1
    dict_str = string[start:end]
    dict_str = dict_str.replace('null', 'None')
    d = ast.literal_eval(dict_str)

    if flip:
        d = {value: key for key, value in d.items()}
    return d


def get_df_chunks(df, chunk_size):
    num_chunks = len(df) // chunk_size + (len(df) % chunk_size > 0)
    chunks = np.array_split(df, num_chunks)
    return [chunk.to_csv(index=False) for chunk in chunks]


def extract_df_from_str(response_str):
    if 'merchant,avg_amount,num_transactions,category' in response_str:
        start_idx = response_str.index('merchant,avg_amount,num_transactions,category')
        csv_data = response_str[start_idx:]
        df = pd.read_csv(StringIO(csv_data))
        return df
    else:
        raise ValueError("CSV data marker not found in the response")


def ai_get_merchants_categories(merchant_summary_df, ai_config, client):

    chunks = get_df_chunks(merchant_summary_df, ai_config.CHUNK_SIZE)

    for chunk in chunks:
        query = ai_queries.get_categories_query(chunk)
        response_str = utils_ai.query_ai(query, ai_config, client)
        chunk_df = extract_df_from_str(response_str)

        chunk_df = chunk_df.dropna(subset=['category'])
        if not chunk_df.empty:
            merchant_summary_df = merchant_summary_df.merge(chunk_df[['merchant', 'category']],
                                                            on='merchant',
                                                            how='left',
                                                            suffixes=('', '_updated'))
            condition = merchant_summary_df['category_updated'].notna()
            merchant_summary_df.loc[condition, 'category'] = merchant_summary_df.loc[condition, 'category_updated']
            merchant_summary_df.drop(columns=['category_updated'], inplace=True)

    return merchant_summary_df


def get_df_mask(df, column_name):
    mask = (df[column_name].isna() |
            (df[column_name] == '') |
            (df[column_name] == ','))
    return mask
