import plotly.express as px
import streamlit as st
from constants import ColumnNames


def plot_pie_chart(df_grouped):
    fig = px.pie(
        df_grouped,
        values='cost',
        names='category',
        title='Expenses by Category',
        width=1000,
        height=1000,
        hole=0.4
    )

    fig.update_traces(textinfo='label+percent', insidetextorientation='radial',
                      texttemplate='%{label}<br>%{value:.2f}€  -  %{percent}')

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


def plot_bar_chart(monthly_expenses):
    fig = px.bar(
        monthly_expenses,
        x='month',
        y=ColumnNames.COST,
        color='category',
        title='Monthly Expenses by Category',
        labels={'month': 'Month', 'cost': 'Expenses (€)'},
        height=600,
        text=ColumnNames.COST
    )

    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Expenses',
        barmode='stack',
        xaxis={'type': 'category'},
        legend_title='Categories'
    )

    st.plotly_chart(fig)
