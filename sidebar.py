import streamlit as st
import pandas as pd
import utils_html
import utils


def apply_date_filter(df):
    return filter_df_by_date_range(df)


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


def get_min_max_date(df):
    min_date = utils.get_date_col_as_datetime(df).min().date()
    max_date = utils.get_date_col_as_datetime(df).max().date()
    return min_date, max_date


def apply_category_filter(df, selected_categories):
    df = df[df['category'].apply(lambda x: x in selected_categories and selected_categories[x])]
    return df


def manage_sidebar_categories(categories_dict):
    st.markdown(utils_html.custom_css_sidebar(), unsafe_allow_html=True)
    st.sidebar.header("Categories")
    selected_categories = {}

    # Buttons for Select All and Unselect All
    col_btn1, col_btn2 = st.sidebar.columns([1, 1])
    if col_btn1.button('Select All'):
        for category in categories_dict.keys():
            st.session_state[f'checkbox_{category}'] = True
        st.experimental_rerun()
    if col_btn2.button('None'):
        for category in categories_dict.keys():
            st.session_state[f'checkbox_{category}'] = False
        st.experimental_rerun()

    # Display categories with checkboxes and trash icons
    for category in categories_dict.keys():
        col1, col2 = st.sidebar.columns([1, 10])

        # HTML for trash icon
        trash_icon_html = utils_html.generate_trash_icon_html(category)
        col1.markdown(trash_icon_html, unsafe_allow_html=True)

        # Initialize or retrieve checkbox state from session state
        if f'checkbox_{category}' not in st.session_state:
            st.session_state[f'checkbox_{category}'] = True  # Default value initialization

        # Checkbox for category selection
        selected_categories[category] = col2.checkbox(category,
                                                      value=st.session_state[f'checkbox_{category}'],
                                                      key=f'checkbox_{category}')

    new_category = st.sidebar.text_input("Add new category")
    if st.sidebar.button("Add Category"):
        sorted_categories = utils.add_new_category(categories_dict, new_category)
        if sorted_categories != categories_dict:
            categories_dict = sorted_categories
            st.sidebar.success(f"Category '{new_category}' added.")
            st.experimental_rerun()

    return selected_categories, categories_dict
