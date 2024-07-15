# Expenses Analyzer Dashboard

This project provides a Streamlit-based dashboard for processing and visualizing expense data from CSV files.   
The dashboard allows users to upload multiple CSV files, filter data by date range and categories, 
and visualize expenses through interactive pie and bar charts.

## Features

- **Upload and Process CSV Files**: Upload multiple CSV files and process them into a single DataFrame.
- **Category Management**: Add and delete categories dynamically.
- **Data Filtering**: Filter data by date range and selected categories.
- **Data Visualization**: Visualize expenses by category and over time using pie and bar charts.
- **Download Processed Data**: Download the processed and concatenated DataFrame as a CSV file.

## Usage
- Upload CSV files via the interface.
- Use the sidebar to filter data by date range and categories.
- View and interact with the visualizations.
- Download the processed data as a CSV file.


## License

This project is licensed under the MIT License. 

## To Do
- Add rows to categories functionality.
- Add checks that api responses match table size (and maybe loop).
- Test if works - Avoid long api call of standardize merchant name if merchant name is not new.
- Improve user messages/instructions/workflow.
- Create functionality of category edits - add and delete.
- Save categories json function?
- Add per category - merchant as hue plot.
- Add list of merchants per category.
- Add number of transactions per category plot.
- Set up a streamlit server.
- genAI - set quotas.
- Test Claude / Llama / Mistral API calls and pricing.
- Test downloaded LLM model instead of API calls.