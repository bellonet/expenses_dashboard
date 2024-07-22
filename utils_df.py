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


def get_monthly_expense_df(df, df_grouped):
    df['month'] = utils.get_date_col_as_datetime(df).dt.to_period('M').astype(str)
    monthly_expenses = df.groupby(['month', ColumnNames.CATEGORY])[ColumnNames.AMOUNT].sum().reset_index()
    category_order = df_grouped.sort_values(by=ColumnNames.AMOUNT, ascending=False)[ColumnNames.CATEGORY].tolist()
    monthly_expenses[ColumnNames.CATEGORY] = pd.Categorical(monthly_expenses[ColumnNames.CATEGORY],
                                                            categories=category_order,
                                                            ordered=True)
    return monthly_expenses
