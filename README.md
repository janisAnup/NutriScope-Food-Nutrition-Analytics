# NutriScope – Food Product & Nutrition Analytics

NutriScope is an interactive Streamlit dashboard for exploring food product records and nutritional characteristics using a cleaned sample of the Open Food Facts dataset.

## Features
- Interactive filters for country, food group, category, energy and protein
- KPI summary for product count and average nutritional values
- Searchable product table and descriptive statistics
- Bar chart, monthly record-creation line chart and nutrition scatter plot
- Data-quality information and filtered CSV export

## Project files
- `app.py` – Streamlit application
- `nutriscope_cleaned.csv` – cleaned analytical dataset (required at runtime)
- `requirements.txt` – Python dependencies

## Run locally
Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the dashboard:

```bash
python -m streamlit run app.py
```

The CSV file must be in the same folder as `app.py`.

## Dataset notes
The dashboard uses a 50,000-record working sample prepared from the downloaded Open Food Facts dataset. Nutritional values are expressed per 100 g. Energy is converted from kJ to kcal. The timeline reflects database record creation dates, not product sales or manufacturing dates.

## Deployment
Connect this repository to Streamlit Community Cloud and set the main file path to `app.py`.
