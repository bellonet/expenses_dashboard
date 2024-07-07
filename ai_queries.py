def get_column_names_query(names):
    query = (f'For the following column names, output only the one (not a list) best column names that correspond to '
             f'"cost", "date" and "text" in a form of a dictionary. \n\n{"\n".join(names)}')
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
