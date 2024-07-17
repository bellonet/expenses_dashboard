import pandas as pd
import streamlit as st
import numpy as np
import re
import logging
from constants import ColumnNames
import utils


def get_min_max_date(df):
    min_date = utils.get_date_col_as_datetime(df).min().date()
    max_date = utils.get_date_col_as_datetime(df).max().date()
    return min_date, max_date


def filter_df_by_date_range(df):

    min_date, max_date = get_min_max_date(df)
    date_range = st.sidebar.date_input("Select date range:", [min_date, max_date])

    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)

        return df[(utils.get_date_col_as_datetime(df) >= start_date) & (utils.get_date_col_as_datetime(df) <= end_date)]
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
        file_list = '<br>'.join(st.session_state.uploaded_files)
        st.write(f"Uploaded files:<br>{file_list}", unsafe_allow_html=True)

        if st.button("Start Over"):
            set_upload_csv_state()
            st.experimental_rerun()

    return st.session_state.all_dfs


def set_upload_csv_state():
    st.session_state.is_uploaded = False
    st.session_state.all_dfs = []
    st.session_state.uploaded_files = []


def save_df_to_csv(df):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download current CSV",
                       data=csv,
                       file_name='expenses_formated.csv',
                       mime='text/csv')
    st.warning('''Save your work by downloading the CSV  
                Make sure you don't select unwanted filters!''')


def get_monthly_expense_df(df, df_grouped):
    df['month'] = utils.get_date_col_as_datetime(df).dt.to_period('M').astype(str)
    monthly_expenses = df.groupby(['month', ColumnNames.CATEGORY])[ColumnNames.AMOUNT].sum().reset_index()
    category_order = df_grouped.sort_values(by=ColumnNames.AMOUNT, ascending=False)[ColumnNames.CATEGORY].tolist()
    monthly_expenses[ColumnNames.CATEGORY] = pd.Categorical(monthly_expenses[ColumnNames.CATEGORY],
                                                            categories=category_order,
                                                            ordered=True)
    return monthly_expenses


def get_df_mask(df, column_name):
    mask = (df[column_name].isna() |
            (df[column_name] == '') |
            (df[column_name] == ','))
    return mask


def ai_add_and_standardize_merchants(df, ai_config, client):
    first_mask = None
    for i in range(4):
        mask = get_df_mask(df, ColumnNames.MERCHANT)
        if i == 0:
            first_mask = mask
        texts_list = df.loc[mask, ColumnNames.TEXT].tolist()
        if texts_list:
            df.loc[mask, ColumnNames.MERCHANT] = utils.ai_get_merchants_from_text(texts_list, ai_config, client)

    if first_mask is not None:
        masked_merchants = df.loc[first_mask, ColumnNames.MERCHANT].tolist()
        standardized_merchants = utils.standardize_merchant_names(masked_merchants)
        df.loc[first_mask, ColumnNames.MERCHANT] = standardized_merchants

    merchants = df[ColumnNames.MERCHANT].tolist()
    merchants = utils.ai_standardize_merchant_names(merchants, ai_config, client)

    return merchants


def get_merchants_summary_df(df):
    merchants_summary_df = df.groupby(ColumnNames.MERCHANT).agg({
        ColumnNames.AMOUNT: ['mean', 'count'],
        ColumnNames.CATEGORY: lambda x: x.mode()[0] if not x.mode().empty else np.nan
    }).reset_index()
    merchants_summary_df.columns = ['merchant', 'avg_amount', 'num_transactions', 'category']
    return merchants_summary_df


def propagate_df_merchant_categories(df):
    valid_categories = df[~df[ColumnNames.CATEGORY].isin([np.nan, None, ''])]
    unique_categories = valid_categories.groupby(ColumnNames.MERCHANT)[ColumnNames.CATEGORY].nunique()
    single_category_merchants = unique_categories[unique_categories == 1].index
    valid_single_categories = valid_categories[valid_categories[ColumnNames.MERCHANT].isin(single_category_merchants)]
    merchant_to_category = valid_single_categories.groupby(ColumnNames.MERCHANT)[ColumnNames.CATEGORY].first().to_dict()
    df[ColumnNames.CATEGORY] = df.apply(lambda row: merchant_to_category.get(row[ColumnNames.MERCHANT],
                                                                             row[ColumnNames.CATEGORY]), axis=1)

    return df


def populate_categories(df, merchants_summary_df):
    df = df.merge(merchants_summary_df[['merchant', 'category']], on='merchant', how='left', suffixes=('', '_updated'))
    mask = get_df_mask(df, ColumnNames.CATEGORY)
    if df['category'].dtype != df['category_updated'].dtype:
        df['category_updated'] = df['category_updated'].astype(df['category'].dtype)
    df.loc[mask, 'category'] = df.loc[mask, 'category_updated']
    df.drop(columns=['category_updated'], inplace=True)
    return df


def ai_get_merchants_categories(merchant_summary_df, ai_config, client):
    mask = get_df_mask(merchant_summary_df, 'category')
    masked_merchant_summary_df = merchant_summary_df[mask]
    if not mask.empty:
        merchant_summary_df.loc[mask, 'category'] = utils.ai_get_merchants_categories(masked_merchant_summary_df,
                                                                                      ai_config,
                                                                                      client)
    return merchant_summary_df


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
