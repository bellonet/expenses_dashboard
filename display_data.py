import streamlit as st
import utils
import utils_io
import utils_df
import plots
from constants import ColumnNames


def display_data(df):
    st.dataframe(df)
    utils_io.save_df_to_csv(df)
    df = utils.invert_amounts(df, ColumnNames.AMOUNT)
    plots.display_summary_metrics(df)

    category_color_map = plots.generate_color_map(df, ColumnNames.CATEGORY)

    df_grouped = df.groupby(ColumnNames.CATEGORY)[ColumnNames.AMOUNT].sum().reset_index()

    if not df_grouped.empty:
        plots.plot_pie_chart(df_grouped, category_color_map)

        monthly_expenses = utils_df.get_monthly_expense_df(df, df_grouped)
        plots.plot_bar_chart(monthly_expenses, category_color_map)
    else:
        st.write("No valid data to plot.")


def display_filtered_df(df, date_filtered_df):
    date_filtered_df = st.data_editor(date_filtered_df)
    df.loc[date_filtered_df.index] = date_filtered_df
    return df
