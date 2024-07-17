import streamlit as st
import logging
import numpy as np
import re
from constants import ColumnNames, Globals
import ai_queries
import utils_ai
import utils


def add_merchants_and_categories(df, ai_config, client):
    message_placeholder = st.empty()
    message_placeholder.info((f"Processing merchant names from transaction texts and sorting to categories. " 
                              f"This may take a couple of minutes.. "
                              f"It's good time to make a coffee or go to the pull-up bar."))
    logging.info("Starting ai merchant extraction process.")

    if 'is_ran_ai' not in st.session_state:
        df[ColumnNames.MERCHANT] = ai_add_and_standardize_merchants(df, ai_config, client)
        df = propagate_df_merchant_categories(df)
        df.to_csv('temp_df_with_categories_prop.csv', index=False)
        merchants_summary_df = get_merchants_summary_df(df)
        merchants_summary_df.to_csv('temp_merchant_summary.csv', index=False)

        merchants_summary_df = ai_get_merchants_categories(merchants_summary_df, ai_config, client)
        df = populate_categories(df, merchants_summary_df)

        st.session_state.is_ran_ai = True
        st.session_state.current_df = df

    else:
        merchants_summary_df = get_merchants_summary_df(df)

    message_placeholder.empty()

    return df, merchants_summary_df


def ai_add_and_standardize_merchants(df, ai_config, client):
    first_mask = None
    for i in range(4):
        mask = utils.get_df_mask(df, ColumnNames.MERCHANT)
        if i == 0:
            first_mask = mask
        texts_list = df.loc[mask, ColumnNames.TEXT].tolist()
        if texts_list:
            df.loc[mask, ColumnNames.MERCHANT] = ai_get_merchants_from_text(texts_list, ai_config, client)

    if first_mask is not None:
        masked_merchants = df.loc[first_mask, ColumnNames.MERCHANT].tolist()
        standardized_merchants = standardize_merchant_names(masked_merchants)
        df.loc[first_mask, ColumnNames.MERCHANT] = standardized_merchants

    merchants = df[ColumnNames.MERCHANT].tolist()
    merchants = ai_standardize_merchant_names(merchants, ai_config, client)

    return merchants


def propagate_df_merchant_categories(df):
    valid_categories = df[~df[ColumnNames.CATEGORY].isin([np.nan, None, ''])]
    unique_categories = valid_categories.groupby(ColumnNames.MERCHANT)[ColumnNames.CATEGORY].nunique()
    single_category_merchants = unique_categories[unique_categories == 1].index
    valid_single_categories = valid_categories[valid_categories[ColumnNames.MERCHANT].isin(single_category_merchants)]
    merchant_to_category = valid_single_categories.groupby(ColumnNames.MERCHANT)[ColumnNames.CATEGORY].first().to_dict()
    df[ColumnNames.CATEGORY] = df.apply(lambda row: merchant_to_category.get(row[ColumnNames.MERCHANT],
                                                                             row[ColumnNames.CATEGORY]), axis=1)

    return df


def get_merchants_summary_df(df):
    merchants_summary_df = df.groupby(ColumnNames.MERCHANT).agg({
        ColumnNames.AMOUNT: ['mean', 'count'],
        ColumnNames.CATEGORY: lambda x: x.mode()[0] if not x.mode().empty else np.nan
    }).reset_index()
    merchants_summary_df.columns = ['merchant', 'avg_amount', 'num_transactions', 'category']
    return merchants_summary_df


def ai_get_merchants_categories(merchant_summary_df, ai_config, client):
    mask = utils.get_df_mask(merchant_summary_df, 'category')
    masked_merchant_summary_df = merchant_summary_df[mask]
    if not mask.empty:
        merchant_summary_df.loc[mask, 'category'] = ai_get_merchants_categories(masked_merchant_summary_df,
                                                                                ai_config,
                                                                                client)
    return merchant_summary_df


def populate_categories(df, merchants_summary_df):
    df = df.merge(merchants_summary_df[['merchant', 'category']], on='merchant', how='left', suffixes=('', '_updated'))
    mask = utils.get_df_mask(df, ColumnNames.CATEGORY)
    if df['category'].dtype != df['category_updated'].dtype:
        df['category_updated'] = df['category_updated'].astype(df['category'].dtype)
    df.loc[mask, 'category'] = df.loc[mask, 'category_updated']
    df.drop(columns=['category_updated'], inplace=True)
    return df


def ai_get_merchants_from_text(texts_list, ai_config, client):

    all_merchants = []

    chunks = utils.get_list_chunks(texts_list, ai_config.CHUNK_SIZE)

    for chunk in chunks:

        merchants = get_merchant_chunk(chunk, ai_config, client)
        all_merchants.extend(merchants)

    logging.info("ai merchant extraction completed.")

    return all_merchants


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
    standardized_merchants_dict = utils.get_dict_from_string(standardized_merchants_str)
    return standardized_merchants_dict


def ai_standardize_merchant_names(merchants, ai_config, client):
    merchants_set_list = sorted(list(set(merchants)))
    merchants_set_list = [item for item in merchants_set_list if not re.search(r'[A-Z]', item)]
    chunks = utils.get_list_chunks(merchants_set_list, ai_config.CHUNK_SIZE)
    standardized_merchants_dict = {}

    for chunk in chunks:
        standardized_merchants_dict.update(standardize_merchant_chunk(chunk, ai_config, client))

    standardized_merchants = [standardized_merchants_dict[merchant]
                              if merchant in standardized_merchants_dict else merchant for merchant in merchants]
    return standardized_merchants


def get_merchant_chunk(chunk, ai_config, client):
    query = ai_queries.get_merchants_query(chunk)
    merchants_str = utils_ai.query_ai(query, ai_config, client)
    merchants = merchants_str.strip().splitlines()

    # merchants = [re.sub(r'^[\d.-]*\s*|\*+$', '', merchant) for merchant in merchants]
    merchants = [re.sub(r'^\d+\.\s*|\*+', '', merchant) for merchant in merchants]
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
