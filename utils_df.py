import pandas as pd
import streamlit as st
import numpy as np
import re
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
