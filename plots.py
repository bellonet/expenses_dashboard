import plotly.express as px
import streamlit as st
from constants import ColumnNames
import df_utils


def display_summary_metrics(df):
    # Calculate the total expenses
    total_expenses = df[ColumnNames.COST].sum()

    min_date, max_date = df_utils.get_min_max_date(df)

    num_months = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1
    num_days = (max_date - min_date).days + 1

    avg_expenses_per_month = total_expenses / num_months
    avg_expenses_per_day = total_expenses / num_days

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.metric(label="Total Expenses", value=f"${total_expenses:,.2f}")
    col2.metric(label="Average Expenses per Month", value=f"${avg_expenses_per_month:,.2f}")
    col3.metric(label="Average Expenses per Day", value=f"${avg_expenses_per_day:,.2f}")


def plot_pie_chart(df_grouped, category_color_map):
    fig = px.pie(
        df_grouped,
        values='cost',
        names='category',
        title='Expenses by Category',
        width=1000,
        height=1000,
        hole=0.4,
        color='category',
        color_discrete_map=category_color_map
    )

    fig.update_traces(
        textinfo='label+percent',
        insidetextorientation='radial',
        texttemplate='%{label}<br>%{value:.2f}€  -  %{percent}',
        hovertemplate='%{label}<br>%{value:.2f}€<br>%{percent}'
    )

    fig.update_layout(
        legend_title="Categories",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig)


def plot_bar_chart(monthly_expenses, category_color_map):

    monthly_expenses.rename(columns={'category': 'cate'}, inplace=True)

    fig = px.bar(
        monthly_expenses,
        x='month',
        y=ColumnNames.COST,
        color='cate',
        title='Monthly Expenses by Category',
        labels={'month': 'Month', ColumnNames.COST: 'Expenses (€)'},
        height=600,
        text=ColumnNames.COST,
        color_discrete_map=category_color_map
    )

    # Update traces for custom hover information
    fig.update_traces(
        texttemplate='%{y:.2f}€',  # Display only the cost on the bar
        hovertemplate='<b>Month: %{x}</b><br>Expense: %{y:.2f}€'
    )

    # Layout adjustments
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Expenses',
        barmode='stack',
        xaxis={'type': 'category'},
        legend_title='Categories'
    )

    # Calculate and display total per month
    for month, group in monthly_expenses.groupby('month'):
        total_expenses = group[ColumnNames.COST].sum()
        fig.add_annotation(
            x=month,
            y=total_expenses,
            text=f'<b>{total_expenses:.2f}€</b>',
            showarrow=False,
            yshift=30,
            font=dict(
                size=14,
                color='green',
            )

        )

    st.plotly_chart(fig)
