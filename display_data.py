import streamlit as st


def display_filtered_df(df, date_filtered_df):
    date_filtered_df = st.data_editor(date_filtered_df)
    df.loc[date_filtered_df.index] = date_filtered_df
    return df
