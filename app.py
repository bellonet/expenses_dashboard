import streamlit as st
import pandas as pd
import utils
import preprocess_df
from preprocess_merchants_categories import add_merchants_and_categories
import utils_io
import sidebar
import display_data
from settings import set_logger, set_st, set_footer, get_ai_config


logger = set_logger()
ai_config = get_ai_config("genai")
ai_client = ai_config.set_client()

set_st()
if 'current_df' in st.session_state:
    df = st.session_state.current_df
else:
    df = pd.DataFrame()
    all_dfs = utils_io.upload_csvs_to_dfs()

    if all_dfs:
        placeholder = st.empty()
        valid_dfs = preprocess_df.format_columns_all_dfs(all_dfs, placeholder.container, ai_config, ai_client)
        if len(valid_dfs) == len(all_dfs):
            placeholder.empty()
            df = preprocess_df.concatenate_dfs(valid_dfs)
            st.session_state.current_df = df

utils.add_categories_to_session_state(df)
#
if not df.empty and 'categories' in st.session_state:
    df, merchants_summary_df = add_merchants_and_categories(df, ai_config, ai_client)
    # df = utils_df.delete_rows(df, to_del_substr_l)
    st.write("You can edit your table here:")

    date_filtered_df = sidebar.apply_date_filter(df)
    if not date_filtered_df.empty:
        selected_categories, categories = sidebar.manage_sidebar_categories(df)
        date_and_categories_filtered_df = sidebar.apply_category_filter(date_filtered_df, selected_categories)

        display_data.display_data(date_and_categories_filtered_df)
    else:
        st.write("No valid data to display.")

    set_footer()
