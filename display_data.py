import streamlit as st
import utils
import utils_io
import utils_df
import plots
from constants import ColumnNames


def display_data(df):
    # st.dataframe(df)
    display_filtered_df(df)

    utils_io.save_df_to_csv(df)
    df = utils.invert_amounts(df, ColumnNames.AMOUNT)
    plots.display_summary_metrics(df)

    category_color_map = plots.generate_color_map(df, ColumnNames.CATEGORY)

    df_grouped = df.groupby(ColumnNames.CATEGORY)[ColumnNames.AMOUNT].sum().reset_index()
    # if df_grouped has negative values - st write warning and delete those from the df:

    print(df_grouped.amount.to_list())
    print(df_grouped.category.to_list())

    if df_grouped[ColumnNames.AMOUNT].lt(0).any():
        st.write("Warning: Negative values detected in the data. Removing those values.")
        df_grouped = df_grouped[df_grouped[ColumnNames.AMOUNT] >= 0]

    print(df_grouped.amount.to_list())
    print(df_grouped.category.to_list())

    if not df_grouped.empty:
        plots.plot_pie_chart(df_grouped, category_color_map)

        monthly_expenses = utils_df.get_monthly_expense_df(df, df_grouped)
        plots.plot_bar_chart(monthly_expenses, category_color_map)
    else:
        st.write("No valid data to plot.")


def display_filtered_df(df):
    date_filtered_df = st.data_editor(df)
    df.loc[date_filtered_df.index] = df
    return df
