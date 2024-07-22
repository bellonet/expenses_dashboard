import streamlit as st
import pandas as pd
from constants import ColumnNames
import utils


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

        st.write(f"Please note: if you close or refresh this page, all unsaved changes will be lost.",
                 unsafe_allow_html=True)

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
