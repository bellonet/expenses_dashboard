def generate_trash_icon_html(category):
    return f'''
    <button class="trash-button" style="border:none;background:none;padding:0;margin-top:5px;vertical-align:middle;" 
    onclick="if(confirm('Are you sure you want to delete category \'{category}\'?')) {{
        fetch('/delete_category', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{'category': '{category}'}})
        }});
    }}">
        <i class="fas fa-trash-alt" style="font-size: 11px;"></i>
    </button>
    '''


def custom_css_sidebar():
    css = """
    <style>
        /* Reduce the gap between elements in the vertical blocks */
        [data-testid='column'] [data-testid='stVerticalBlock'] {
            gap: 0rem !important;
            margin-top: -13px !important;
            margin-bottom: -13px !important;
        }

        div.stButton > button:first-child {
            background-color: None !important;
            border: None;
            color: green;
            margin: 10px 0px 10px 0px;
        }

    </style>
    """
    return css
