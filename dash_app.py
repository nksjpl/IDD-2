# dash_app.py
import os
import json
import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# ─── Data Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'california_infectious_diseases.csv')
GEOJSON_PATH = os.path.join(BASE_DIR, 'california-counties.geojson')

# ─── Load Data ──────────────────────────────────────────────────────────────
if not os.path.exists(CSV_PATH) or not os.path.exists(GEOJSON_PATH):
    raise FileNotFoundError('CSV or GeoJSON file not found in project directory')

# Master DataFrame
df = pd.read_csv(CSV_PATH)
# GeoJSON for choropleth
with open(GEOJSON_PATH) as f:
    counties_geo = json.load(f)

# ─── Filter Options ─────────────────────────────────────────────────────────
diseases = ['All Diseases'] + sorted(df['Disease'].unique())
counties = ['All Counties'] + sorted(df['County'].unique())
years = ['All Years'] + sorted(df['Year'].astype(str).unique())
sexes = ['All'] + sorted(df['Sex'].unique())

# ─── Dash App Initialization ─────────────────────────────────────────────────
app = dash.Dash(__name__, title='California Infectious Disease Dashboard')
server = app.server

# ─── App Layout ──────────────────────────────────────────────────────────────
app.layout = html.Div([
    # Header
    html.Div([
        html.H2('California Infectious Disease Dashboard', style={'margin': '0'}),
        html.P('Data from 2001–2023 (Provisional)', style={'margin': '0', 'color':'gray'})
    ], style={'textAlign':'center', 'padding':'20px'}),

    # Filters
    html.Div([
        html.Div([
            html.Label('Disease'),
            dcc.Dropdown(id='disease-filter', options=[{'label':d,'value':d} for d in diseases], value='All Diseases', clearable=False)
        ], style={'width':'24%', 'display':'inline-block'}),
        html.Div([
            html.Label('County'),
            dcc.Dropdown(id='county-filter', options=[{'label':c,'value':c} for c in counties], value='All Counties', clearable=False)
        ], style={'width':'24%', 'display':'inline-block'}),
        html.Div([
            html.Label('Year'),
            dcc.Dropdown(id='year-filter', options=[{'label':y,'value':y} for y in years], value='All Years', clearable=False)
        ], style={'width':'24%', 'display':'inline-block'}),
        html.Div([
            html.Label('Sex'),
            dcc.Dropdown(id='sex-filter', options=[{'label':s,'value':s} for s in sexes], value='All', clearable=False)
        ], style={'width':'24%', 'display':'inline-block'}),
        html.Button('Clear Filters', id='clear-button', n_clicks=0, style={'marginLeft':'20px','backgroundColor':'#FF4B4B','color':'white','border':'none','padding':'8px 16px','borderRadius':'4px'})
    ], style={'backgroundColor':'#f0f2f5','padding':'15px','borderRadius':'6px','boxShadow':'0 2px 4px rgba(0,0,0,0.1)','margin':'20px'}),

    # Metrics cards
    html.Div(id='cards-container', style={'display':'flex','justifyContent':'space-between','margin':'20px'}),

    # Charts area
    html.Div([
        html.Div(dcc.Graph(id='bar-chart'), style={'width':'65%','display':'inline-block','verticalAlign':'top'}),
        html.Div(dcc.Graph(id='map-chart'), style={'width':'33%','display':'inline-block','verticalAlign':'top','paddingLeft':'10px'})
    ], style={'margin':'20px'}),

    # Line chart
    html.Div(dcc.Graph(id='line-chart'), style={'margin':'20px'})
], style={'fontFamily':'Arial, sans-serif','backgroundColor':'#ffffff'})

# ─── Clear Filters Callback ─────────────────────────────────────────────────
def reset_filters(n_clicks):
    return 'All Diseases','All Counties','All Years','All'

app.callback(
    [Output('disease-filter', 'value'),
     Output('county-filter', 'value'),
     Output('year-filter', 'value'),
     Output('sex-filter', 'value')],
    Input('clear-button','n_clicks')
)(reset_filters)

# ─── Main Update Callback ──────────────────────────────────────────────────
@app.callback(
    [Output('cards-container','children'),
     Output('bar-chart','figure'),
     Output('map-chart','figure'),
     Output('line-chart','figure')],
    [Input('disease-filter','value'),
     Input('county-filter','value'),
     Input('year-filter','value'),
     Input('sex-filter','value')]
)
def update_dashboard(disease, county, year, sex):
    # Filter DataFrame
    dff = df.copy()
    if disease!='All Diseases': dff = dff[dff['Disease']==disease]
    if county != 'All Counties': dff = dff[dff['County']==county]
    if year   != 'All Years':    dff = dff[dff['Year']==int(year)]
    if sex    != 'All':         dff = dff[dff['Sex']==sex]

    # Cards
    total = dff['Cases'].sum()
    first = dff['Year'].min() if not dff.empty else None
    last  = dff['Year'].max() if not dff.empty else None
    cards = [
        html.Div([
            html.P('Total Cases', style={'margin':'0','color':'gray'}),
            html.H3(f"{total:,}", style={'margin':'5px 0','color':'#4e50ff'})
        ], style={'flex':'1','padding':'20px','backgroundColor':'#ffffff','borderRadius':'6px','boxShadow':'0 1px 3px rgba(0,0,0,0.1)','textAlign':'center'}),
        html.Div([
            html.P('First Reported Year', style={'margin':'0','color':'gray'}),
            html.H3(f"{first}", style={'margin':'5px 0','color':'#4e50ff'})
        ], style={'flex':'1','padding':'20px','backgroundColor':'#ffffff','borderRadius':'6px','boxShadow':'0 1px 3px rgba(0,0,0,0.1)','textAlign':'center'}),
        html.Div([
            html.P('Last Reported Year', style={'margin':'0','color':'gray'}),
            html.H3(f"{last}", style={'margin':'5px 0','color':'#4e50ff'})
        ], style={'flex':'1','padding':'20px','backgroundColor':'#ffffff','borderRadius':'6px','boxShadow':'0 1px 3px rgba(0,0,0,0.1)','textAlign':'center'})
    ]

    # Bar chart
    bar_data = dff.groupby('Year')['Cases'].sum().reset_index()
    fig_bar = px.bar(bar_data, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, title='Filtered Data Breakdown', template='plotly_white')
    fig_bar.update_layout(margin={'t':40,'l':40,'r':20,'b':40})

    # Map chart
    map_data = dff.groupby('County')['Cases'].sum().reset_index()
    map_data['County'] = map_data['County'].str.title()
    fig_map = px.choropleth_mapbox(
        map_data, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
        color='Cases', hover_data=['County','Cases'], mapbox_style='carto-positron',
        center={'lat':37.5,'lon':-119.5}, zoom=5, opacity=0.6, title='Cases by County Map', template='plotly_white'
    )
    fig_map.update_layout(margin={'t':40,'l':0,'r':0,'b':0})

    # Line chart
    fig_line = px.area(bar_data, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, title='Cases Over Time', template='plotly_white')
    fig_line.update_layout(margin={'t':40,'l':40,'r':20,'b':40})

    return [cards, fig_bar, fig_map, fig_line]

# ─── Main ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run_server(debug=True)
