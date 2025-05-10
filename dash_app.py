import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import json

# Load data from provided files
csv_path = '/mnt/data/california_infectious_diseases.csv'
geojson_path = '/mnt/data/california-counties.geojson'

df = pd.read_csv(csv_path)
with open(geojson_path) as f:
    counties_geo = json.load(f)

# Prepare filter options
diseases = ['All Diseases'] + sorted(df['Disease'].unique().tolist())
counties = ['All Counties'] + sorted(df['County'].unique().tolist())
years = ['All Years'] + sorted(df['Year'].astype(str).unique().tolist())
sexes = ['All'] + sorted(df['Sex'].unique().tolist())

# Dash app setup
app = dash.Dash(__name__)
app.title = 'California Infectious Disease Dashboard'

card_style = {
    'flex': '1',
    'padding': '20px',
    'margin': '10px',
    'backgroundColor': 'white',
    'borderRadius': '5px',
    'textAlign': 'center',
    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
}

# Layout
app.layout = html.Div([
    html.H1('California Infectious Disease Dashboard', style={'textAlign': 'center'}),
    html.Div('Data from 2001-2023 (Provisional)', style={'textAlign': 'center', 'color': 'gray'}),

    # Filters
    html.Div([
        html.Div([
            html.Label('Disease'),
            dcc.Dropdown(id='disease-filter', options=[{'label': d, 'value': d} for d in diseases], value='All Diseases')
        ], style={'width': '24%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.Label('County'),
            dcc.Dropdown(id='county-filter', options=[{'label': c, 'value': c} for c in counties], value='All Counties')
        ], style={'width': '24%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.Label('Year'),
            dcc.Dropdown(id='year-filter', options=[{'label': y, 'value': y} for y in years], value='All Years')
        ], style={'width': '24%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.Label('Sex'),
            dcc.Dropdown(id='sex-filter', options=[{'label': s, 'value': s} for s in sexes], value='All')
        ], style={'width': '24%', 'display': 'inline-block', 'padding': '10px'}),
        html.Button('Clear Filters', id='clear-button', n_clicks=0,
                    style={'backgroundColor': '#FF6361', 'color': 'white', 'padding': '10px', 'border': 'none', 'borderRadius': '5px', 'margin': '10px'})
    ], style={'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'padding': '10px', 'display': 'flex', 'justifyContent': 'space-between'}),

    # Cards
    html.Div(id='cards-container', style={'display': 'flex', 'justifyContent': 'space-around', 'padding': '20px'}),

    # Charts: Bar + Map
    html.Div([
        html.Div(dcc.Graph(id='bar-chart'), style={'width': '60%'}),
        html.Div(dcc.Graph(id='map-chart'), style={'width': '38%'})
    ], style={'display': 'flex', 'justifyContent': 'space-between'}),

    # Line chart
    html.Div(dcc.Graph(id='line-chart'), style={'padding': '20px'})
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#EFEFEF'})

# Callback to clear filters
def reset_values(n_clicks):
    return 'All Diseases', 'All Counties', 'All Years', 'All'

app.callback(
    [Output('disease-filter', 'value'),
     Output('county-filter', 'value'),
     Output('year-filter', 'value'),
     Output('sex-filter', 'value')],
    Input('clear-button', 'n_clicks')
)(reset_values)

# Main update callback
@app.callback(
    [Output('cards-container', 'children'),
     Output('bar-chart', 'figure'),
     Output('map-chart', 'figure'),
     Output('line-chart', 'figure')],
    [Input('disease-filter', 'value'),
     Input('county-filter', 'value'),
     Input('year-filter', 'value'),
     Input('sex-filter', 'value')]
)
def update_dashboard(disease, county, year, sex):
    dff = df.copy()
    if disease != 'All Diseases':
        dff = dff[dff['Disease'] == disease]
    if county != 'All Counties':
        dff = dff[dff['County'] == county]
    if year != 'All Years':
        dff = dff[dff['Year'] == int(year)]
    if sex != 'All':
        dff = dff[dff['Sex'] == sex]

    # Cards
    total = dff['Cases'].sum()
    first = dff['Year'].min() if not dff.empty else None
    last = dff['Year'].max() if not dff.empty else None
    cards = [
        html.Div([html.Div('Total Cases'), html.H3(f"{total:,}", style={'color': '#4e50ff'})], style=card_style),
        html.Div([html.Div('First Reported Year'), html.H3(f"{first}", style={'color': '#4e50ff'})], style=card_style),
        html.Div([html.Div('Last Reported Year'), html.H3(f"{last}", style={'color': '#4e50ff'})], style=card_style)
    ]

    # Bar Chart
    bar_data = dff.groupby('Year')['Cases'].sum().reset_index()
    fig_bar = px.bar(bar_data, x='Year', y='Cases', title='Filtered Data Breakdown')
    fig_bar.update_layout(xaxis_title='Year', yaxis_title='Number of Cases')

    # Map
    map_data = dff.groupby('County')['Cases'].sum().reset_index()
    fig_map = px.choropleth_mapbox(
        map_data, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
        color='Cases', hover_data=['County','Cases'],
        mapbox_style='carto-positron', zoom=5, center={'lat':37.5,'lon':-119.5}, opacity=0.6,
        title='Cases by County Map'
    )
    fig_map.update_layout(margin={'r':0,'t':30,'l':0,'b':0})

    # Line Chart
    line_data = bar_data.sort_values('Year')
    fig_line = px.area(line_data, x='Year', y='Cases', title='Cases Over Time')
    fig_line.update_layout(xaxis_title='Year', yaxis_title='Number of Cases')

    return cards, fig_bar, fig_map, fig_line

if __name__ == '__main__':
    app.run_server(debug=True)
