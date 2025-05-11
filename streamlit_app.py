# streamlit_app.py
import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# ─── Page Configuration and Styling ─────────────────────────────────────────
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .filter-box {background-color: #f0f2f5; padding: 16px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;}
      .metric-card {background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;}
      .metric-label {font-size: 0.9rem; color: #6b7280; margin: 0;}
      .metric-value {font-size: 1.5rem; color: #4e50ff; margin: 4px 0 0 0;}
      .section-title {font-size: 1.25rem; margin: 10px 0; font-weight: 600;}
      body {background-color: #ffffff;}
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Data Loading ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
csv_path = os.path.join(BASE_DIR, 'california_infectious_diseases.csv')
geojson_path = os.path.join(BASE_DIR, 'california-counties.geojson')
if not os.path.exists(csv_path) or not os.path.exists(geojson_path):
    st.error("Missing data files. Ensure 'california_infectious_diseases.csv' and 'california-counties.geojson' are present.")
    st.stop()

# master DataFrame
df = pd.read_csv(csv_path)
# geojson
with open(geojson_path) as f:
    counties_geo = json.load(f)

# ─── Sidebar Filters ─────────────────────────────────────────────────────────
st.sidebar.header("Filters")
# Default values for filters
defaults = {
    'disease': 'All Diseases',
    'county':  'All Counties',
    'year':    'All Years',
    'sex':     'All'
}
# initialize session state
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# options
disease_opts = ['All Diseases'] + sorted(df['Disease'].unique())
county_opts  = ['All Counties'] + sorted(df['County'].unique())
year_opts    = ['All Years'] + sorted(df['Year'].astype(str).unique())
sex_opts     = ['All'] + sorted(df['Sex'].unique())

# selectboxes with current state as default
st.session_state['disease'] = st.sidebar.selectbox(
    "Disease", disease_opts,
    index=disease_opts.index(st.session_state['disease']), key='disease'
)
st.session_state['county'] = st.sidebar.selectbox(
    "County", county_opts,
    index=county_opts.index(st.session_state['county']), key='county'
)
st.session_state['year'] = st.sidebar.selectbox(
    "Year", year_opts,
    index=year_opts.index(st.session_state['year']), key='year'
)
st.session_state['sex'] = st.sidebar.selectbox(
    "Sex", sex_opts,
    index=sex_opts.index(st.session_state['sex']), key='sex'
)

# clear filters button
if st.sidebar.button("Clear Filters"):
    for key, val in defaults.items():
        st.session_state[key] = val
    st.experimental_rerun()

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("# California Infectious Disease Dashboard")
st.markdown("*Data from 2001–2023 (Provisional)*")

# ─── Filter Data ────────────────────────────────────────────────────────────
dff = df.copy()
if st.session_state['disease'] != defaults['disease']:
    dff = dff[dff['Disease'] == st.session_state['disease']]
if st.session_state['county']  != defaults['county']:
    dff = dff[dff['County'] == st.session_state['county']]
if st.session_state['year']    != defaults['year']:
    dff = dff[dff['Year'] == int(st.session_state['year'])]
if st.session_state['sex']     != defaults['sex']:
    dff = dff[dff['Sex'] == st.session_state['sex']]

# ─── Metrics Cards ─────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3, gap='large')

total_cases = dff['Cases'].sum()
first_year  = int(dff['Year'].min()) if not dff.empty else 'N/A'
last_year   = int(dff['Year'].max()) if not dff.empty else 'N/A'

with col1:
    st.markdown(
        f"<div class='metric-card'><p class='metric-label'>Total Cases</p><p class='metric-value'>{total_cases:,}</p></div>",
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f"<div class='metric-card'><p class='metric-label'>First Reported Year</p><p class='metric-value'>{first_year}</p></div>",
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        f"<div class='metric-card'><p class='metric-label'>Last Reported Year</p><p class='metric-value'>{last_year}</p></div>",
        unsafe_allow_html=True
    )

# ─── Charts Section ─────────────────────────────────────────────────────────
# Bar + Map in two columns
chart_col, map_col = st.columns([2,1], gap='large')

# Bar chart: Filtered Data Breakdown
df_bar = dff.groupby('Year')['Cases'].sum().reset_index()
fig_bar = px.bar(
    df_bar, x='Year', y='Cases', title='Filtered Data Breakdown',
    labels={'Cases':'Number of Cases'}, template='plotly_white'
)
with chart_col:
    st.plotly_chart(fig_bar, use_container_width=True)

# Map chart: Cases by County
map_df = dff.groupby('County', as_index=False)['Cases'].sum()
map_df['County'] = map_df['County'].str.title()
fig_map = px.choropleth_mapbox(
    map_df, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
    color='Cases', hover_data=['County','Cases'], mapbox_style='carto-positron',
    center={'lat':37.5, 'lon':-119.5}, zoom=5, opacity=0.6, title='Cases by County Map',
    template='plotly_white'
)
with map_col:
    st.plotly_chart(fig_map, use_container_width=True)

# Line chart: Cases Over Time
st.markdown("<div class='section-title'>Cases Over Time</div>", unsafe_allow_html=True)
fig_line = px.area(
    df_bar, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, template='plotly_white'
)
st.plotly_chart(fig_line, use_container_width=True)
