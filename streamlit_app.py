# streamlit_app.py
import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# ─── Page Configuration & Styling ──────────────────────────────────────────
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")

# Hide default Streamlit elements and apply container styles
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .dashboard-card {background-color: #ffffff; padding: 1rem; border-radius: 0.75rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom:1rem;}
      .metric-title {font-size: 0.9rem; color: #6b7280; margin-bottom: 0.25rem;}
      .metric-value {font-size: 1.75rem; color: #4e50ff; margin:0;}
      .section-header {font-size:1.5rem; font-weight:600; margin-top:1.5rem; margin-bottom:0.5rem;}
      body {background-color: #f3f4f6;}
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Data Loading ──────────────────────────────────────────────────────────
base = os.path.dirname(__file__)
csv_file = os.path.join(base, 'california_infectious_diseases.csv')
geo_file = os.path.join(base, 'california-counties.geojson')

if not os.path.exists(csv_file):
    st.error(f"❌ Missing CSV at {csv_file}")
    st.stop()
if not os.path.exists(geo_file):
    st.error(f"❌ Missing GeoJSON at {geo_file}")
    st.stop()

df = pd.read_csv(csv_file)
with open(geo_file) as f:
    counties_geo = json.load(f)

# ─── Filters (Sidebar) ──────────────────────────────────────────────────────
st.sidebar.header("Filters")

# Default values
defaults = {
    'disease': 'All Diseases',
    'county':  'All Counties',
    'year':    'All Years',
    'sex':     'All'
}

# Initialize session state
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Options
options = {
    'disease': ['All Diseases'] + sorted(df['Disease'].unique()),
    'county':  ['All Counties'] + sorted(df['County'].unique()),
    'year':    ['All Years'] + sorted(df['Year'].astype(str).unique()),
    'sex':     ['All'] + sorted(df['Sex'].unique())
}

# Sidebar widgets
st.session_state['disease'] = st.sidebar.selectbox("Disease", options['disease'], index=options['disease'].index(st.session_state['disease']))
st.session_state['county']  = st.sidebar.selectbox("County",  options['county'],  index=options['county'].index(st.session_state['county']))
st.session_state['year']    = st.sidebar.selectbox("Year",    options['year'],    index=options['year'].index(st.session_state['year']))
st.session_state['sex']     = st.sidebar.selectbox("Sex",     options['sex'],     index=options['sex'].index(st.session_state['sex']))

if st.sidebar.button("Clear Filters"):
    for key, val in defaults.items():
        st.session_state[key] = val
    st.experimental_rerun()

# ─── Main Layout ────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>California Infectious Disease Dashboard</div>", unsafe_allow_html=True)
st.markdown("*Data from 2001–2023 (Provisional)*")

# Filter DataFrame
dff = df.copy()
if st.session_state['disease'] != defaults['disease']:
    dff = dff[dff['Disease'] == st.session_state['disease']]
if st.session_state['county']  != defaults['county']:
    dff = dff[dff['County']  == st.session_state['county']]
if st.session_state['year']    != defaults['year']:
    dff = dff[dff['Year'] == int(st.session_state['year'])]
if st.session_state['sex']     != defaults['sex']:
    dff = dff[dff['Sex'] == st.session_state['sex']]

# ─── Metrics Cards ─────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3, gap='medium')

total = dff['Cases'].sum()
first = int(dff['Year'].min()) if not dff.empty else 'N/A'
last = int(dff['Year'].max())  if not dff.empty else 'N/A'

with col1:
    st.markdown(f"<div class='dashboard-card'><p class='metric-title'>Total Cases</p><p class='metric-value'>{total:,}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='dashboard-card'><p class='metric-title'>First Reported Year</p><p class='metric-value'>{first}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='dashboard-card'><p class='metric-title'>Last Reported Year</p><p class='metric-value'>{last}</p></div>", unsafe_allow_html=True)

# ─── Charts ─────────────────────────────────────────────────────────────────
chart1, chart2 = st.columns([2,1], gap='large')

# Bar Chart
bar_df = dff.groupby('Year')['Cases'].sum().reset_index()
fig_bar = px.bar(bar_df, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, title='Filtered Data Breakdown', template='plotly_white')
with chart1:
    st.plotly_chart(fig_bar, use_container_width=True)

# Map Chart
map_df = dff.groupby('County')['Cases'].sum().reset_index()
fig_map = px.choropleth_mapbox(
    map_df, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
    color='Cases', hover_data=['County','Cases'], mapbox_style='carto-positron',
    center={'lat':37.5,'lon':-119.5}, zoom=5, opacity=0.6, title='Cases by County Map', template='plotly_white'
)
fig_map.update_layout(margin={'r':0,'t':30,'l':0,'b':0})
with chart2:
    st.plotly_chart(fig_map, use_container_width=True)

# Line Chart
st.markdown("<div class='section-header'>Cases Over Time</div>", unsafe_allow_html=True)
fig_line = px.area(bar_df, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, template='plotly_white')
st.plotly_chart(fig_line, use_container_width=True)
