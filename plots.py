import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from constants import ColumnNames
import sidebar
from constants import PlotSettings


def generate_color_map(df, column):
    unique_categories = sorted(df[column].unique())
    return {category: color for category, color in zip(unique_categories, PlotSettings.DEFAULT_COLORS)}


def display_summary_metrics(df):
    # Calculate the total expenses
    total_expenses = df[ColumnNames.AMOUNT].sum()

    min_date, max_date = sidebar.get_min_max_date(df)

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
    st.markdown("<br>", unsafe_allow_html=True)
    fig = px.pie(
        df_grouped,
        values=ColumnNames.AMOUNT,
        names=ColumnNames.CATEGORY,
        width=1000,
        height=1000,
        hole=0.4,
        color=ColumnNames.CATEGORY,
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
        ),
        title=dict(
            text='Expenses by Category',
            font=dict(size=PlotSettings.TITLE_SIZE)
        ),
        font=dict(size=PlotSettings.LABEL_SIZE)
    )

    st.plotly_chart(fig)


def plot_bar_chart(monthly_expenses, category_color_map):

    monthly_expenses.rename(columns={'category': 'cate'}, inplace=True)

    fig = px.bar(
        monthly_expenses,
        x='month',
        y=ColumnNames.AMOUNT,
        color='cate',
        title='Monthly Expenses by Category',
        labels={'month': 'Month', ColumnNames.AMOUNT: 'Expenses (€)'},
        height=600,
        text=ColumnNames.AMOUNT,
        category_orders={'cate': list(monthly_expenses['cate'].cat.categories)},
        color_discrete_map=category_color_map
    )

    fig.update_traces(
        texttemplate='%{y:.2f}€',
        hovertemplate='<b>Month: %{x}</b><br>Expense: %{y:.2f}€'
    )

    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Expenses',
        barmode='stack',
        xaxis={'type': 'category'},
        legend_title='Categories',
        title=dict(
            text='Expenses by Category',
            font=dict(size=PlotSettings.TITLE_SIZE)
        ),
        font=dict(size=PlotSettings.LABEL_SIZE)
    )

    for month, group in monthly_expenses.groupby('month'):
        total_expenses = group[ColumnNames.AMOUNT].sum()
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


def plot_sunburst_merchants_and_categories(df, category_color_map):
    grouped_df = df.groupby(['category', 'merchant'], as_index=False).sum()

    # Creating the sunburst chart
    fig = px.sunburst(
        grouped_df,
        path=['category', 'merchant'],
        values='amount',
        color='category',
        color_discrete_map=category_color_map,
        width=1000,
        height=1000,
        branchvalues='total'
    )

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig)
