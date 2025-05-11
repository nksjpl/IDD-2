# dash_app.py
import os
import json
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# ─── App Initialization ─────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'california_infectious_diseases.csv')
GEOJSON_PATH = os.path.join(BASE_DIR, 'california-counties.geojson')

# Load and validate data
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"Data file not found: {CSV_PATH}")
if not os.path.exists(GEOJSON_PATH):
    raise FileNotFoundError(f"GeoJSON file not found: {GEOJSON_PATH}")

df = pd.read_csv(CSV_PATH)
with open(GEOJSON_PATH) as f:
    counties_geo = json.load(f)

# Instantiate Dash with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title='CA Infectious Disease Dashboard'
)
server = app.server

# ─── Compute Filter Options ─────────────────────────────────────────────────
options = {
    'disease': ['All Diseases'] + sorted(df['Disease'].unique()),
    'county': ['All Counties'] + sorted(df['County'].unique()),
    'year':   ['All Years'] + sorted(df['Year'].astype(str).unique()),
    'sex':    ['All'] + sorted(df['Sex'].unique())
}

# ─── Shared Styles ──────────────────────────────────────────────────────────
CARD_STYLE = {'borderRadius': '0.5rem', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'padding': '1rem'}
HEADER_STYLE = {'marginTop': '2rem', 'marginBottom': '1rem'}

# ─── Layout ─────────────────────────────────────────────────────────────────
app.layout = dbc.Container([  
    # Title
    dbc.Row(dbc.Col(html.H1("California Infectious Disease Dashboard", className='text-center'), width=12), style=HEADER_STYLE),
    dbc.Row(dbc.Col(html.P("Data from 2001–2023 (Provisional)", className='text-center text-muted'), width=12)),

    # Filters
    dbc.Card([
        dbc.Row([
            dbc.Col([html.Label('Disease'), dcc.Dropdown(id='disease-filter', options=[{'label':d,'value':d} for d in options['disease']], value=options['disease'][0])], width=3),
            dbc.Col([html.Label('County'),  dcc.Dropdown(id='county-filter',  options=[{'label':c,'value':c} for c in options['county']],   value=options['county'][0])],  width=3),
            dbc.Col([html.Label('Year'),    dcc.Dropdown(id='year-filter',    options=[{'label':y,'value':y} for y in options['year']],     value=options['year'][0])],     width=3),
            dbc.Col([html.Label('Sex'),     dcc.Dropdown(id='sex-filter',     options=[{'label':s,'value':s} for s in options['sex']],      value=options['sex'][0])],      width=3)
        ], align='center', form=True),
        dbc.Button('Clear Filters', id='clear-filters', color='danger', outline=True, className='mt-3')
    ], className='mb-4', style=CARD_STYLE),

    # Summary Cards
    dbc.Row([
        dbc.Col(dbc.Card([html.H6('Total Cases'), html.H2(id='total-cases', className='text-primary')], style=CARD_STYLE), width=4),
        dbc.Col(dbc.Card([html.H6('First Reported Year'), html.H2(id='first-year', className='text-primary')], style=CARD_STYLE), width=4),
        dbc.Col(dbc.Card([html.H6('Last Reported Year'), html.H2(id='last-year',  className='text-primary')], style=CARD_STYLE), width=4)
    ], className='mb-4'),

    # Charts
    dbc.Row([
        dbc.Col(dcc.Graph(id='bar-chart', config={'displayModeBar':False}), width=8),
        dbc.Col(dcc.Graph(id='map-chart', config={'displayModeBar':False}), width=4)
    ], className='mb-4'),
    dbc.Row(dbc.Col(dcc.Graph(id='area-chart', config={'displayModeBar':False}), width=12)),

], fluid=True)

# ─── Callbacks ──────────────────────────────────────────────────────────────
@app.callback(
    [Output('total-cases', 'children'),
     Output('first-year',   'children'),
     Output('last-year',    'children'),
     Output('bar-chart',    'figure'),
     Output('map-chart',    'figure'),
     Output('area-chart',   'figure')],
    [Input('disease-filter', 'value'),
     Input('county-filter',  'value'),
     Input('year-filter',    'value'),
     Input('sex-filter',     'value'),
     Input('clear-filters',  'n_clicks')]
)
def update_dashboard(disease, county, year, sex, clear_clicks):
    # Reset if clear clicked
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('clear-filters'):
        return (f"0", 'N/A', 'N/A', {}, {}, {})

    # Filter data
    dff = df.copy()
    if disease  and disease!='All Diseases': dff = dff[dff['Disease']==disease]
    if county   and county!='All Counties':  dff = dff[dff['County']==county]
    if year     and year!='All Years':      dff = dff[dff['Year']==int(year)]
    if sex      and sex!='All':             dff = dff[dff['Sex']==sex]

    # Metrics
    total = dff['Cases'].sum()
    first = dff['Year'].min() if not dff.empty else 'N/A'
    last  = dff['Year'].max() if not dff.empty else 'N/A'

    # Bar
    bar_df = dff.groupby('Year')['Cases'].sum().reset_index()
    fig_bar = px.bar(bar_df, x='Year', y='Cases', labels={'Cases':'Cases'}, template='simple_white')
    fig_bar.update_layout(margin=dict(t=30,l=0,r=0,b=0))

    # Map
    map_df = dff.groupby('County')['Cases'].sum().reset_index()
    fig_map = px.choropleth_mapbox(
        map_df, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
        color='Cases', hover_data=['Cases'], mapbox_style='carto-positron',
        center={'lat':37.5,'lon':-119.5}, zoom=5, opacity=0.6, template='simple_white'
    )
    fig_map.update_layout(margin=dict(t=30,l=0,r=0,b=0))

    # Area
    fig_area = px.area(bar_df, x='Year', y='Cases', labels={'Cases':'Cases'}, template='simple_white')
    fig_area.update_layout(margin=dict(t=30,l=0,r=0,b=0))

    return f"{total:,}", first, last, fig_bar, fig_map, fig_area

# ─── Entry Point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
