import streamlit as st
import utils
import utils_io
import utils_df
import plots
from constants import ColumnNames


def display_data(filtered_df, df):
    # st.dataframe(df)
    display_filtered_df(filtered_df, df)

    utils_io.save_df_to_csv(filtered_df)
    filtered_df = utils.invert_amounts(filtered_df, ColumnNames.AMOUNT)
    plots.display_summary_metrics(filtered_df)

    category_color_map = plots.generate_color_map(filtered_df, ColumnNames.CATEGORY)

    df_grouped = filtered_df.groupby(ColumnNames.CATEGORY)[ColumnNames.AMOUNT].sum().reset_index()
    # if df_grouped has negative values - st write warning and delete those from the df:

    if df_grouped[ColumnNames.AMOUNT].lt(0).any():
        st.write("Warning: Negative values detected in the data. Removing those values.")
        df_grouped = df_grouped[df_grouped[ColumnNames.AMOUNT] >= 0]

    if not df_grouped.empty:
        plots.plot_pie_chart(df_grouped, category_color_map)

        monthly_expenses = utils_df.get_monthly_expense_df(filtered_df, df_grouped)
        plots.plot_bar_chart(monthly_expenses, category_color_map)

        # if number of unique categories in df is less than 3:
        if filtered_df[ColumnNames.CATEGORY].nunique() <= 3:
            plots.plot_sunburst_merchants_and_categories(filtered_df, category_color_map)
        else:
            st.write("Further charts will be displayed after filtering to less than 3 categories.")

    else:
        st.write("No valid data to plot.")


def display_filtered_df(filtered_df, df):
    filtered_df = st.data_editor(filtered_df)
    df.loc[filtered_df.index] = filtered_df
    st.session_state['current_df'] = df
    return df
