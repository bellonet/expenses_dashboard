import re
import pandas as pd
import streamlit as st
import json
from collections import OrderedDict
from constants import OpenAIConfig, Colors


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


def chunk_texts(texts_list, chunk_size):
    chunks = []
    current_chunk = []

    current_length = 0
    for text in texts_list:
        text_length = len(text)
        if current_length + text_length + 1 > chunk_size:  # +1 for the newline or separator
            chunks.append(current_chunk)
            current_chunk = []
            current_length = 0
        current_chunk.append(text)
        current_length += text_length + 1  # +1 for the newline or separator

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def get_merchants_from_text_chatgpt(texts_list, openai_client):
    display_message(Colors.PRIMARY_COLOR, "Please wait a couple of minutes for ChatGPT to process the table..")
    all_merchants = []

    chunks = chunk_texts(texts_list, OpenAIConfig.CHUNK_SIZE)

    for chunk in chunks:
        messages = [
            {"role": "user",
             "content": f'Please match each transaction with its corresponding merchant in the format "Merchant:"'
                        f'and list only the merchant names from the following transactions:\n\n{". ".join(chunk)}'}
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=OpenAIConfig.MAX_TOKENS,
        )

        merchants = response.choices[0].message.content.strip().split("\n")
        all_merchants.extend(merchants)

    return all_merchants
