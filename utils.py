import logging
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


def manually_match_merchants_and_chunk(merchants, chunk):

    matched_merchants = []
    for text in chunk:
        found = False
        for merchant in merchants:
            if merchant in text:
                matched_merchants.append(merchant)
                found = True
                break
        if not found:
            matched_merchants.append('')

    return matched_merchants


def log_mismatch_to_txt(chunk, merchants):
    with open(Globals.LOG_AI_PATH, 'a') as f:
        f.write('Chunk:\n')
        f.write('\n'.join(chunk))
        f.write('\n\nMerchants:\n')
        f.write('\n'.join(merchants))
        f.write('\n\n')


def get_merchant_chunk(chunk, ai_config, client):
    query = ai_queries.get_merchants_query(chunk)
    merchants_str = utils_ai.query_ai(query, ai_config, client)
    merchants = merchants_str.strip().splitlines()

    merchants = [re.sub(r'^[\d.-]*\s*|\*+$', '', merchant) for merchant in merchants]
    merchants = delete_merchants_from_chunk(merchants)

    if len(merchants) != len(chunk):
        logging.warning(f"Merchant-Chunk length mismatch: {len(merchants)} vs {len(chunk)} - some empty.")
        merchants = manually_match_merchants_and_chunk(merchants, chunk)
        log_mismatch_to_txt(chunk, merchants)

    return merchants


def delete_merchants_from_chunk(merchants):
    merchants = [item for item in merchants if len(item.split()) < Globals.MERCHANTS_MAX_WORDS]
    merchants = [item for item in merchants if item != '']
    return merchants


def ai_get_merchants_from_text(texts_list, ai_config, client):

    all_merchants = []

    chunks = get_list_chunks(texts_list, ai_config.CHUNK_SIZE)

    for chunk in chunks:

        merchants = get_merchant_chunk(chunk, ai_config, client)
        all_merchants.extend(merchants)

    logging.info("ai merchant extraction completed.")

    return all_merchants


def get_dict_from_string(string, flip=False):
    start = string.find('{')
    end = string.find('}') + 1
    dict_str = string[start:end]
    dict_str = dict_str.replace('null', 'None')
    d = ast.literal_eval(dict_str)

    if flip:
        d = {value: key for key, value in d.items()}
    return d


def standardize_merchant_names(merchants):
    merchants = [merchant.lower().strip().replace(',', '').replace("'", '') for merchant in merchants]
    merchants = [merchant.split(' gmbh')[0] for merchant in merchants]
    for n in range(1, 5):
        n_worded_strs = {merchant.lower() for merchant in merchants if len(merchant.split()) == n}
        for s in n_worded_strs:
            for i, merchant in enumerate(merchants):
                if merchant.lower().startswith(s):
                    merchants[i] = s
    return merchants


def standardize_merchant_chunk(chunk, ai_config, client):
    query = ai_queries.get_standardize_merchants_query(chunk)
    standardized_merchants_str = utils_ai.query_ai(query, ai_config, client)
    standardized_merchants_dict = get_dict_from_string(standardized_merchants_str)
    return standardized_merchants_dict


def ai_standardize_merchant_names(merchants, ai_config, client):
    merchants_set_list = sorted(list(set(merchants)))
    merchants_set_list = [item for item in merchants_set_list if not re.search(r'[A-Z]', item)]
    chunks = get_list_chunks(merchants_set_list, ai_config.CHUNK_SIZE)
    standardized_merchants_dict = {}

    for chunk in chunks:
        standardized_merchants_dict.update(standardize_merchant_chunk(chunk, ai_config, client))

    standardized_merchants = [standardized_merchants_dict[merchant]
                              if merchant in standardized_merchants_dict else merchant for merchant in merchants]
    return standardized_merchants


def get_df_chunks(df, chunk_size):
    num_chunks = len(df) // chunk_size + (len(df) % chunk_size > 0)
    print('num chunks', num_chunks)
    print(df)
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
