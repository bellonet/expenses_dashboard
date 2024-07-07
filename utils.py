import logging
import re
import pandas as pd
import streamlit as st
import json
from collections import OrderedDict
import ast
import utils_ai
import ai_queries
from constants import Globals


def str_to_float(value):
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


def read_strs_to_del(json_path='json/delete_list.json'):
    with open(json_path, 'r') as json_file:
        to_del_list = json.load(json_file)
    return to_del_list


def invert_amounts(df, amount_column):
    """Invert the sign of the amount column in the DataFrame."""
    df[amount_column] = -df[amount_column]
    return df


def chunk_texts(texts_list, chunk_size):
    chunks = [texts_list[i:i + chunk_size] for i in range(0, len(texts_list), chunk_size)]
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
    with open(Globals.LOG_MERCHANT_MISMATCH_PATH, 'a') as f:
        f.write('Chunk:\n')
        f.write('\n'.join(chunk))
        f.write('\n\nMerchants:\n')
        f.write('\n'.join(merchants))
        f.write('\n\n')


def process_chunk(chunk, ai_config, client):
    query = ai_queries.get_merchants_query(chunk)
    merchants_str = utils_ai.query_ai(query, ai_config, client)
    merchants = merchants_str.strip().splitlines()

    if len(merchants) != len(chunk):
        logging.warning(f"Merchant-Chunk length mismatch: {len(merchants)} vs {len(chunk)} - some empty.")
        merchants = manually_match_merchants_and_chunk(merchants, chunk)
        log_mismatch_to_txt(chunk, merchants)

    return merchants


def ai_get_merchants_from_text(texts_list, ai_config, client):
    message_placeholder = st.empty()
    message_placeholder.info((f"Processing merchant names from transaction texts. This may take a couple of minutes.. "
                              f"It's good time to make a coffee or go to the pull-up bar."))
    logging.info("Starting ai merchant extraction process.")

    all_merchants = []

    chunks = chunk_texts(texts_list, ai_config.CHUNK_SIZE)

    for chunk in chunks:
        merchants = process_chunk(chunk, ai_config, client)
        all_merchants.extend(merchants)

    all_merchants = [re.sub(r'^[\d.-]*\s*', '', merchant) for merchant in all_merchants]
    logging.info("ai merchant extraction completed.")

    message_placeholder.empty()
    return all_merchants


def standardize_merchant_names(merchants):
    merchants = [merchant.lower() for merchant in merchants]
    merchants = [merchant.split(' gmbh')[0] for merchant in merchants]
    for n in range(1, 5):
        n_worded_strs = {merchant.lower() for merchant in merchants if len(merchant.split()) == n}
        for s in n_worded_strs:
            for i, merchant in enumerate(merchants):
                if merchant.lower().startswith(s):
                    merchants[i] = s
    return merchants


def get_flipped_dict_from_string(string):
    # Extract the dictionary string
    start = string.find('{')
    end = string.find('}') + 1
    dict_str = string[start:end]
    d = ast.literal_eval(dict_str)
    flipped_dict = {value: key for key, value in d.items()}
    return flipped_dict
