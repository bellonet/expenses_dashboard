import streamlit as st


def get_column_names_query(names):
    query = (f"For the following column names, output a dictionary with the keys 'amount', 'date', and 'text'. "
             f"The values should be the closest matching column name, even if the key is the same as a column name. "
             f'Output only dictionary. \n\n{"\n".join(names)}')
    return query


def get_merchants_query(chunk):
    query = (f'For each of the following transaction output the merchant name, '
             f'not the payment gateways or intermediaries like PayPal. Super important rules: '
             f'Exclude other transaction identifiers but keep the core merchant name. '
             f'Super important!! Find the final merchant - as opposed to payment intermediaries like PayPal '
             f'or other gateways unless you really cannot find another merchant in the line.'
             f'Treat every line as a merchant entry, even if it looks like a summary or header. '
             f'The first line should be included as well, no matter what it contains. '
             f'One output per input - total 15 - in given order, never ever miss a line. '
             f'If a transaction is related to a payment gateway like PayPal, '
             f'output the name of the merchant the payment is associated with, not the payment gateway itself.'
             f'\n\n{"\n".join(chunk)}')
    return query


def get_standardize_merchants_query(chunk):
    query = (f'for the following list, correct the merchant name to be the actual short business name. '
             f"Don't relay on common keywords, but on the actual business name (e.g. find restaurant name). " 
             f"form your answer as a dictionary (no explanation or comments): \n\n{"\n".join(chunk)}")
    return query


def get_categories_query(chunk):
    query = (f'possible expenses categories: {",".join(st.session_state.categories)} .\n'
             f'add the missing categories to table based on merchant and the average amount spend/gained. ' 
             f'If you are not 90% sure,leave empty. Answer only with the table with {len(chunk.split('\n'))-2} rows. '
             f'no explanation: \n\n{chunk}')
    return query
