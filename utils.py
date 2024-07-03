import logging
import re
import pandas as pd
import streamlit as st
import json
from collections import OrderedDict
from constants import OpenAIConfig


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


def invert_costs(df, cost_column):
    """Invert the sign of the cost column in the DataFrame."""
    df[cost_column] = -df[cost_column]
    return df


def chunk_texts(texts_list, chunk_size=25):
    chunks = [texts_list[i:i + chunk_size] for i in range(0, len(texts_list), chunk_size)]
    return chunks


def query_chatgpt(query, openai_client):
    messages = [
        {"role": "user",
         "content": query}
    ]
    response = openai_client.chat.completions.create(
        model=OpenAIConfig.MODEL,
        messages=messages,
        max_tokens=OpenAIConfig.MAX_TOKENS,
    )
    merchants = response.choices[0].message.content.strip().split("\n")
    return merchants


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


def get_merchants_from_text_chatgpt(texts_list, openai_client):
    message_placeholder = st.empty()
    message_placeholder.info((f"Processing merchant names from transaction texts. This may take a couple of minutes.. "
                              f"It's good time to make a coffee or go to the pull-up bar."))
    all_merchants = []

    chunks = chunk_texts(texts_list)

    with st.spinner("Processing..."):
        for chunk in chunks:

            query = (f'List the merchant names from the following transactions, '
                     f'exclude other transaction identifiers but keep the core merchant name, keep cities and location.'
                     f'Remove common business suffixes like GmbH unless essential for distinguishing similar names. '
                     'Do not include payment intermediaries like PayPal or other gateways in the output '
                     f'unless you really cannot find the merchant in the text.'
                     f'Treat every line as a merchant entry, even if it looks like a summary or header. '
                     f' The first line should be included as well, no matter what it contains. '
                     f'One output per input - total {len(chunk)} - in order, never miss a line:\n\n{"\n".join(chunk)}')

            merchants = query_chatgpt(query, openai_client)

            if len(merchants) != len(chunk):
                logging.warning(f"Merchant-Chunk length mismatch: {len(merchants)} vs {len(chunk)} - some empty.")
                merchants = manually_match_merchants_and_chunk(merchants, chunk)

                with open('bad_chunk.txt', 'a') as f:
                    f.write('Chunk:\n')
                    f.write('\n'.join(chunk))
                    f.write('\n\nMerchants:\n')
                    f.write('\n'.join(merchants))
                    f.write('\n\n')

            all_merchants.extend(merchants)

        all_merchants = [re.sub(r'^[\d.-]*\s*', '', merchant) for merchant in all_merchants]

    message_placeholder.empty()
    return all_merchants
