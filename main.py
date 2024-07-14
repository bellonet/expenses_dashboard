import streamlit as st
import utils_html
import logging
import pandas as pd
import plots
import utils
import utils_df
from constants import ColumnNames, Colors, get_ai_config, Globals
from plots import plot_pie_chart, plot_bar_chart


def set_logger():
    logger = logging.getLogger()
    if Globals.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def set_st():
    st.set_page_config(layout="wide")
    st.title('Expenses Analyzer')
    st.markdown(
        f'<h4 style="color:{Colors.PRIMARY_COLOR};">Analyze your expenses to make smarter financial decisions.</h4>',
        unsafe_allow_html=True)
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">'
        , unsafe_allow_html=True)

    if 'is_ran_merchant' not in st.session_state:
        st.session_state.is_ran_merchant = False


def set_footer():
    footer = f"""
    <div style="color:{Colors.SECONDARY_TEXT}; width: 100%; text-align: left; padding: 10px 0;">
    <p>Please contact me for any bugs or feature requests: bellonet @ gmail</p>
    <p>Another amazing tool: 
    <a href="https://www.jonathanronen.com/time-to-retirement.html" target="_blank">Time to Retirement Calculator</a>
    , made by my better half ❤️</p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)


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


def display_data(df):
    st.dataframe(df)
    utils_df.save_df_to_csv(df)
    df = utils.invert_amounts(df, ColumnNames.AMOUNT)
    plots.display_summary_metrics(df)

    category_color_map = plots.generate_color_map(df, ColumnNames.CATEGORY)

    df_grouped = df.groupby(ColumnNames.CATEGORY)[ColumnNames.AMOUNT].sum().reset_index()

    if not df_grouped.empty:
        plot_pie_chart(df_grouped, category_color_map)

        monthly_expenses = utils_df.get_monthly_expense_df(df, df_grouped)
        plot_bar_chart(monthly_expenses, category_color_map)
    else:
        st.write("No valid data to plot.")


logger = set_logger()
ai_config = get_ai_config("genai")
ai_client = ai_config.set_client()

categories_dict = utils.read_categories()
to_del_substr_l = utils.read_strs_to_del()

set_st()
if 'current_df' in st.session_state:
    df = st.session_state.current_df
else:
    df = pd.DataFrame()
    all_dfs = utils_df.upload_csvs_to_dfs()
    placeholder = st.empty()

    if all_dfs:
        valid_dfs = utils_df.format_columns_all_dfs(all_dfs, placeholder.container, ai_config, ai_client)
        if len(valid_dfs) == len(all_dfs):
            placeholder.empty()
            df = utils_df.concatenate_dfs(valid_dfs)


utils.add_categories_to_session_state(df)

if not df.empty and 'categories' in st.session_state:
    pass
    df = utils_df.add_merchants(df, ai_config, ai_client)
    # utils_df.add_categories_to_df(df, categories_dict)
    #
    #         date_filtered_df = utils_df.apply_date_filter(df)
    #         selected_categories, categories_dict = manage_sidebar_categories(categories_dict)
    #         df = utils_df.apply_category_filter(date_filtered_df, selected_categories)
    #         df = utils_df.delete_rows(df, to_del_substr_l)
    #
    # if not df.empty:
    #     display_data(df)
    #
    # set_footer()
