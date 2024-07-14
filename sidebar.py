import streamlit as st
import utils_html
import utils


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
