# scripts/dashboard.py
"""
Investor-focused Investment Analysis Dashboard (Dash)

Requirements:
- Reads processed CSVs from processed/
- Shows YoY & QoQ for categories (monthly data)
- Shows YoY for manufacturers (yearly)
- Filters: date range, category, manufacturer
- Charts: trends + % change

Run:
    py scripts\dashboard.py
Then open the address printed (usually http://127.0.0.1:8050/)
"""

import os
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import plotly.express as px
import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc


# pick a Bootstrap theme (FLATLY, LUX, CYBORG, etc.)
BOOTSTRAP_THEME = dbc.themes.FLATLY

# optional: Google font
GOOGLE_FONT = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"

external_stylesheets = [BOOTSTRAP_THEME, GOOGLE_FONT]

# -------------------------
# Build Dash app
# -------------------------

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

# optional: if you want to set meta tags and title
app.title = "Investor Analysis Dashboard"
server = app.server  # for deployment

# Brand / palette (Mapping Your category color(s))

CATEGORY_COLOR_MAP = {
    "FOUR WHEELER (INVALID CARRIAGE)": "#1f77b4",  # Blue
    "HEAVY MOTOR VEHICLE": "#ff7f0e",              # Orange
    "LIGHT MOTOR VEHICLE": "#2ca02c",              # Green
    "MEDIUM MOTOR VEHICLE": "#d62728",             # Red
    "THREE WHEELER (INVALID CARRIAGE)": "#9467bd", # Purple
    "THREE WHEELER(NT)": "#8c564b",                # Brown
    "THREE WHEELER(T)": "#e377c2",                 # Pink
    "TWO WHEELER (INVALID CARRIAGE)": "#7f7f7f",   # Gray
    "TWO WHEELER(NT)": "#bcbd22",                  # Yellow-green
    "TWO WHEELER(T)": "#17becf"                    # Cyan
}


# Apply sensible defaults
px.defaults.template = "plotly_white"


# -------------------------
# Config / file paths
# -------------------------
BASE = Path.cwd()
PROCESSED = BASE / "processed"

CATEGORY_MONTHLY_FILE = PROCESSED / "category_monthly_clean.csv"
CATEGORY_YEARLY_FILE = PROCESSED / "category_yearly_clean.csv"
MFR_2W_FILE = PROCESSED / "manufacturer_2w.csv"
MFR_3W_FILE = PROCESSED / "manufacturer_3w.csv"
MFR_4W_FILE = PROCESSED / "manufacturer_4w.csv"

# -------------------------
# Utility functions
# -------------------------
def safe_read_csv(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)

def prepare_category_monthly(df):
    # Ensure Date column is datetime; if it's a string, parse
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    elif 'MonthRaw' in df.columns:
        df['Date'] = pd.to_datetime(df['MonthRaw'], errors='coerce')
    else:
        # try Year & Month
        if 'Year' in df.columns and 'Month' in df.columns:
            df['Date'] = pd.to_datetime(dict(year=df['Year'], month=df['Month'], day=1))
        else:
            raise ValueError("No Date/MonthRaw/Year+Month in category monthly file")
    df['Registrations'] = pd.to_numeric(df['Registrations'], errors='coerce').fillna(0).astype(int)
    # canonical Category column name
    if 'Category' not in df.columns:
        # infer first text column as Category
        text_cols = [c for c in df.columns if df[c].dtype == object]
        if len(text_cols) > 0:
            df.rename(columns={text_cols[0]: 'Category'}, inplace=True)
    return df.sort_values(['Category', 'Date']).reset_index(drop=True)

def compute_category_yoy_qoq(df):
    # Ensure date column is in datetime format
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort values to ensure correct pct_change calculation
    df = df.sort_values(['Category', 'Date']).reset_index(drop=True)

    # Year-over-Year (YoY) percentage change
    df['YoY_pct'] = df.groupby('Category')['Registrations'] \
                      .transform(lambda s: s.pct_change(periods=12) * 100)

    # Quarter-over-Quarter (QoQ) percentage change
    df['QoQ_pct'] = df.groupby('Category')['Registrations'] \
                      .transform(lambda s: s.pct_change(periods=3) * 100)

    # Extract quarter info for grouping if needed
    df['Quarter'] = df['Date'].dt.to_period('Q')

    # Quarterly aggregated dataframe
    df_quarter = (
        df.groupby(['Category', 'Quarter'], as_index=False)['Registrations']
          .sum()
    )

    return df, df_quarter


def prepare_manufacturers():
    # read and concat all manufacturer files
    frames = []
    for f in [MFR_2W_FILE, MFR_3W_FILE, MFR_4W_FILE]:
        if Path(f).exists():
            tmp = pd.read_csv(f)
            frames.append(tmp)
    if not frames:
        raise FileNotFoundError("No manufacturer files found in processed/ (2w/3w/4w).")
    mdf = pd.concat(frames, ignore_index=True)
    # normalize column names
    mdf.columns = [c.strip() for c in mdf.columns]
    # canonicalize Maker column name:
    maker_col = None
    for cand in ['Maker', 'Maker ', 'Maker_Name', 'Manufacturer', 'Maker Name', 'MakerName', 'Maker']:
        if cand in mdf.columns:
            maker_col = cand
            break
    if maker_col is None:
        # pick first non-numeric column
        for c in mdf.columns:
            if mdf[c].dtype == object:
                maker_col = c
                break
    mdf = mdf.rename(columns={maker_col: 'Maker'})
    # ensure Year numeric and Registrations numeric
    if 'Year' in mdf.columns:
        mdf['Year'] = pd.to_numeric(mdf['Year'], errors='coerce').astype('Int64')
    if 'Registrations' in mdf.columns:
        mdf['Registrations'] = pd.to_numeric(mdf['Registrations'], errors='coerce').fillna(0).astype(int)
    # if Category column exists, ensure normalized strings
    if 'Category' in mdf.columns:
        mdf['Category'] = mdf['Category'].astype(str).str.strip()
    else:
        # try to infer category column by searching for common tokens
        for c in mdf.columns:
            if any(tok in c.lower() for tok in ['2w','3w','4w','category','segment']):
                mdf.rename(columns={c:'Category'}, inplace=True)
                break
    return mdf

def compute_manufacturer_yoy(mdf):
    """
    Input: mdf (raw concatenated manufacturer DataFrame)
    Output: DataFrame grouped by Maker/Year/Category with YoY% column
    """
    # ensure numeric types and drop obviously bad rows
    mdf = mdf.copy()
    if 'Year' in mdf.columns:
        mdf['Year'] = pd.to_numeric(mdf['Year'], errors='coerce').astype('Int64')
    if 'Registrations' in mdf.columns:
        mdf['Registrations'] = pd.to_numeric(mdf['Registrations'], errors='coerce').fillna(0).astype(int)

    # aggregate to ensure one row per Maker-Year-Category
    m = (
        mdf
        .groupby(['Maker','Year','Category'], dropna=False, as_index=False)['Registrations']
        .sum()
    )

    # sort and reset index so transform aligns correctly
    m = m.sort_values(['Maker','Year']).reset_index(drop=True)

    # use transform (not apply) so the result aligns with m's index
    m['YoY_pct'] = m.groupby('Maker')['Registrations'].transform(lambda s: s.pct_change(periods=1) * 100)

    return m


# -------------------------
# Load data
# -------------------------
cat_month = prepare_category_monthly(safe_read_csv(CATEGORY_MONTHLY_FILE))
cat_year = safe_read_csv(CATEGORY_YEARLY_FILE)
mfr_all = prepare_manufacturers()

# precompute
cat_month_long, cat_quarter = compute_category_yoy_qoq(cat_month)
mfr_yoy = compute_manufacturer_yoy(mfr_all)



# UI helpers
available_categories = sorted(cat_month['Category'].unique().astype(str))
available_makers = sorted(mfr_all['Maker'].dropna().unique().astype(str))
min_date = cat_month['Date'].min()
max_date = cat_month['Date'].max()

# map user-facing dropdown labels to codes stored in manufacturer_all.csv
CATEGORY_CODE_MAP = {

    # 4-wheelers
    "FOUR WHEELER (INVALID CARRIAGE)": "4WIC",
    "HEAVY MOTOR VEHICLE": "HMV",
    "LIGHT MOTOR VEHICLE": "LMV",
    "MEDIUM MOTOR VEHICLE": "MMV",

    # 3-wheelers
    "THREE WHEELER (INVALID CARRIAGE)": "3WIC",
    "THREE WHEELER(NT)": "3WN",
    "THREE WHEELER(T)": "3WT",

    # 2-wheelers
    "TWO WHEELER (INVALID CARRIAGE)": "2WIC",
    "TWO WHEELER(NT)": "2WN",
    "TWO WHEELER(T)": "2WT",
    
}

def map_dropdown_categories_to_codes(sel_categories):
    """
    sel_categories: None | str | list
    returns list of category codes (e.g. ['4WIC'])
    """
    if not sel_categories:
        return None
    if isinstance(sel_categories, str):
        sel_categories = [sel_categories]

    codes = []
    for c in sel_categories:
        c = str(c).strip()
        code = CATEGORY_CODE_MAP.get(c)
        if code:
            codes.append(code)
        else:
            # fallback: if no mapping exists, try exact value (maybe user already supplied code)
            codes.append(c)
    return codes



app.layout = dbc.Container([
    # Title
    dbc.Row([
        dbc.Col([
            html.H1("Investor Analysis DashBoard", className="text-center mt-1"),
            html.P("Clean summary of YoY / QoQ growth and market share. Use filters to explore.",
                   className="text-center text-muted mb-4")
        ])
    ]),

    # Filters Card
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Date Range (Monthly)", className="fw-bold"),
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=min_date,
                        max_date_allowed=max_date,
                        start_date=min_date,
                        end_date=max_date,
                        display_format='YYYY-MM',
                        style={'width': '120%'}
                    )
                ], md=3),

                dbc.Col([
                    html.Label("Category (Multi)", className="fw-bold"),
                    dcc.Dropdown(
                        id='category-filter',
                        options=[{'label': c, 'value': c} for c in available_categories],
                        value=None, multi=True, clearable=False,
                        style={'width': '100%'}
                    )
                ], md=4),

                dbc.Col([
                    html.Label("Manufacturer", className="fw-bold"),
                    dcc.Dropdown(
                        id='maker-filter',
                        options=[],
                        value=None,
                        multi=False,
                        placeholder="Select maker (Highest-Lowest)",
                        clearable=True,
                          style={'width': '100%'}
                    )
                ], md=5)
            ], className="gy-3")
        ])
    ], className="mb-4 shadow-sm"),

    # Graphs: Monthly Trends + YoY
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([dcc.Graph(id='monthly-trend')])
            ], className="shadow-sm mb-4")
        ], md=12),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([dcc.Graph(id='monthly-yoy')])
            ], className="shadow-sm mb-4")
        ], md=12),
    ]),

    # Graphs: QoQ + Top Makers
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([dcc.Graph(id='quarterly-qoq')])
            ], className="shadow-sm mb-4")
        ], md=6),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([dcc.Graph(id='top-makers')])
            ], className="shadow-sm mb-4")
        ], md=6)
    ]),

    # Manufacturer Details
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Manufacturer Trend & YoY", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='maker-yearly'),
                    html.Label("Select year for market share pie:", className="fw-bold mt-3"),
                    dcc.Dropdown(
                        id='share-year',
                        options=[{'label': y, 'value': int(y)} for y in sorted(cat_year['Year'].unique())],
                        value=int(cat_year['Year'].max()),
                        style={'width': '300px'}
                    )
                ])
            ], className="shadow-sm mb-4")
        ])
    ]),

    html.Div(id='debug', style={'display': 'none'})
], fluid=True)


# -------------------------
# Callbacks
# -------------------------
# -------------------------

#  callback for updating main charts 

@app.callback(
    Output('monthly-trend', 'figure'),
    Output('monthly-yoy', 'figure'),
    Output('quarterly-qoq', 'figure'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('category-filter', 'value'),
    Input('maker-filter', 'value')
)
def update_main_charts(start_date, end_date, categories, maker_selected):
    # Ensure categories is list
    if isinstance(categories, str):
        categories = [categories]

    # --------------------
    # Monthly data filtering
    # --------------------
    d = cat_month_long.copy()
    d = d[(d['Date'] >= pd.to_datetime(start_date)) & (d['Date'] <= pd.to_datetime(end_date))]
    if categories:
        d = d[d['Category'].isin(categories)]

    # Monthly trend
    fig_trend = px.line(
        d, x='Date', y='Registrations', color='Category',
        title='Monthly registrations by category', markers=False
    )
    # fig_trend.update_layout(legend={'orientation': 'h', 'y': -0.2})

    fig_trend.update_layout(
    template="plotly_white",
    font_family="Inter, Arial, sans-serif",
    title_x=0.02,  # align left slightly
    margin=dict(t=40, l=20, r=20, b=20),
    legend={'orientation': 'h', 'y': -0.2}
)

    # Monthly YoY
    d_yoy = d.sort_values(['Category', 'Date']).copy()
    d_yoy['YoY_pct'] = d_yoy.groupby('Category')['Registrations'] \
                            .transform(lambda s: s.pct_change(periods=12) * 100)
    fig_yoy = px.bar(d_yoy, x='Date', y='YoY_pct', color='Category', title='Monthly YoY % change (by category)', color_discrete_map=CATEGORY_COLOR_MAP)
    fig_yoy.update_layout(
    template="plotly_white",
    font_family="Inter, Arial, sans-serif",
    title_x=0.02,  # align left slightly
    margin=dict(t=40, l=20, r=20, b=20),
    yaxis_title='YoY %'
)


    # Quarterly QoQ
    q = d.copy()
    q['Quarter'] = q['Date'].dt.to_period('Q')
    qagg = q.groupby(['Category', 'Quarter'], as_index=False)['Registrations'].sum()
    qagg = qagg.sort_values(['Category', 'Quarter'])
    qagg['QoQ_pct'] = qagg.groupby('Category')['Registrations'] \
                          .transform(lambda s: s.pct_change(periods=1) * 100)
    qagg['QuarterStart'] = qagg['Quarter'].dt.start_time
    fig_qoq = px.bar(qagg, x='QuarterStart', y='QoQ_pct', color='Category', title='Quarterly QoQ % change by category', color_discrete_map=CATEGORY_COLOR_MAP)
    fig_qoq.update_layout(
    template="plotly_white",
    font_family="Inter, Arial, sans-serif",
    title_x=0.02,  # align left slightly
    margin=dict(t=40, l=20, r=20, b=20),
    yaxis_title='QoQ %', 
    xaxis_title='Quarter')
    

    return fig_trend, fig_yoy, fig_qoq


#  callback for updating manufacturer chart 
@app.callback(
    Output('maker-yearly', 'figure'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('category-filter', 'value'),
    Input('maker-filter', 'value')
)
def update_maker_yearly(start_date, end_date, categories, maker_selected):
    # copy dataset
    df = mfr_all.copy()

    # map dropdown categories to csv codes
    category_codes = map_dropdown_categories_to_codes(categories)  # None or list of codes

    # Ensure columns exist and normalize types
    if 'Category' not in df.columns:
        return px.bar(title="manufacturer_all is missing 'Category' column")
    if 'Maker' not in df.columns:
        return px.bar(title="manufacturer_all is missing 'Maker' column")
    if 'Year' not in df.columns:
        return px.bar(title="manufacturer_all is missing 'Year' column")

    df['Category'] = df['Category'].astype(str).str.strip()
    df['Maker'] = df['Maker'].astype(str).str.strip()
    # ensure Year numeric
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    # apply category filter (use codes)
    if category_codes:
        df = df[df['Category'].isin(category_codes)]

    # apply maker filter
    if maker_selected:
        df = df[df['Maker'] == str(maker_selected).strip()]

    # apply year range from date picker
    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    df = df[(df['Year'] >= start_year) & (df['Year'] <= end_year)]

    # If empty, return friendly message/chart
    if df.empty:
        return px.bar(title="No data for selected filters")

    # aggregate registrations per Year
    yearly_data = df.groupby('Year', as_index=False)['Registrations'].sum().sort_values('Year')

    fig = px.bar(
        yearly_data,
        x='Year',
        y='Registrations',
        title=f"{maker_selected or 'All Makers'} — {', '.join(category_codes) if category_codes else 'All Categories'}",
        labels={'Registrations': 'Total Registrations'},
        text='Registrations',
         color_discrete_map=CATEGORY_COLOR_MAP
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        template="plotly_white",
        font_family="Inter, Arial, sans-serif",
        title_x=0.02,  # align left slightly
        margin=dict(t=40, l=20, r=20, b=20),
        yaxis_title='Registrations')

    return fig


#  callback for updating top 10 manufacturer chart
@app.callback(
    Output('top-makers', 'figure'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('category-filter', 'value'),
    Input('maker-filter', 'value')
)
def update_top_makers(start_date, end_date, categories, maker_selected):
    # Map UI categories to internal codes
    category_codes = map_dropdown_categories_to_codes(categories)

    # Load manufacturer data
    df = mfr_all.copy()

    # Filter by category
    if category_codes:
        df = df[df['Category'].isin(category_codes)]

    # Filter by maker
    if maker_selected:
        df = df[df['Maker'] == maker_selected]

    # Filter by year range
    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    if 'Year' in df.columns:
        df = df[(df['Year'] >= start_year) & (df['Year'] <= end_year)]

    # Aggregate and get top 10 makers
    top_makers = (
        df.groupby('Maker', as_index=False)['Registrations']
        .sum()
        .sort_values('Registrations', ascending=False)
        .head(10)
    )

    # Create bar chart
    fig = px.bar(
        top_makers,
        x='Registrations',
        y='Maker',
        orientation='h',
        title='Top 10 Makers',
         color_discrete_map=CATEGORY_COLOR_MAP
    )
    fig.update_layout(
        template="plotly_white",
        font_family="Inter, Arial, sans-serif",
        title_x=0.02,  # align left slightly
        margin=dict(t=40, l=20, r=20, b=20),
        yaxis={'categoryorder': 'total ascending'})

    return fig


#  callback for dynamic manufacturer dropdown 
@app.callback(
    Output('maker-filter', 'options'),
    Output('maker-filter', 'value'),  # Added for stale handling
    Input('category-filter', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    State('maker-filter', 'value')  # Keep track of current selection
)
def update_maker_dropdown(selected_categories, start_date, end_date, current_maker):
    # Map category names to codes
    category_codes = map_dropdown_categories_to_codes(selected_categories)

    df = mfr_all.copy()

    # Filter by category
    if category_codes:
        df = df[df['Category'].isin(category_codes)]

    # Filter by date range if 'Year' column exists
    if 'Year' in df.columns and start_date and end_date:
        start_year = pd.to_datetime(start_date).year
        end_year = pd.to_datetime(end_date).year
        df = df[(df['Year'] >= start_year) & (df['Year'] <= end_year)]

      # Filter out manufacturers with > 0 registrations
        df = df[df['Registrations'] > 0]    

    # Sort manufacturers by total registrations (descending)
    makers_sorted = (
        df.groupby('Maker')['Registrations']
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    options = [{'label': m, 'value': m} for m in makers_sorted]

    # Handle stale selection — clear if no longer valid
    if current_maker not in makers_sorted:
        return options, None
    else:
        return options, current_maker




# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
