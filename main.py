import streamlit as st
import html_utils
import logging
import utils
import df_utils
from constants import ColumnNames
from plots import plot_pie_chart, plot_bar_chart


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info("Logging test")
    return logger


def set_st():
    st.set_page_config(layout="wide")
    st.title('Expenses Analyzer')
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">',
        unsafe_allow_html=True)


# Function to manage sidebar categories
def manage_sidebar_categories(categories_dict):
    st.markdown(html_utils.custom_css_sidebar(), unsafe_allow_html=True)

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
        trash_icon_html = html_utils.generate_trash_icon_html(category)
        col1.markdown(trash_icon_html, unsafe_allow_html=True)

        # Checkbox for category selection
        selected_categories[category] = col2.checkbox(category, value=True, key=f'checkbox_{category}')

    # Input for adding new categories
    new_category = st.sidebar.text_input("Add new category")
    if st.sidebar.button("Add Category"):
        if new_category and new_category not in categories_dict:
            categories_dict[new_category] = new_category
            st.sidebar.success(f"Category '{new_category}' added.")

    return selected_categories


def display_data(df):
    st.dataframe(df.head(10))

    df_grouped = df.groupby('category')[ColumnNames.COST].sum().reset_index()
    df_grouped[ColumnNames.COST] = df_grouped[ColumnNames.COST].abs()

    if not df_grouped.empty:
        plot_pie_chart(df_grouped)
    else:
        st.write("No valid data to plot.")

    if not df.empty:
        df['month'] = df_utils.get_date_col_as_datetime(df).dt.to_period('M').astype(str)
        monthly_expenses = df.groupby(['month', 'category'])[ColumnNames.COST].sum().abs().reset_index()
        plot_bar_chart(monthly_expenses)
    else:
        st.write("No data available for the selected date range to plot.")


logger = set_logger()
# Reading initial data
categories_dict = utils.read_categories()
to_del_substr_l = utils.read_strs_to_del()

set_st()
all_dfs = df_utils.upload_csvs_to_dfs()
placeholder = st.empty()

if all_dfs:
    valid_dfs = df_utils.rename_columns_all_dfs(all_dfs, placeholder.container)
    if len(valid_dfs) == len(all_dfs):
        placeholder.empty()
        df = df_utils.concatenate_dfs(valid_dfs)
        df_utils.add_categories_to_df(df, categories_dict)

        date_filtered_df = df_utils.apply_date_filter(df)
        selected_categories = manage_sidebar_categories(categories_dict)
        df = df_utils.apply_category_filter(date_filtered_df, selected_categories)
        df = df_utils.delete_rows(df, to_del_substr_l)

        st.dataframe(df)
        df_utils.save_df_to_csv(df)

        if not df.empty:
            display_data(df)
