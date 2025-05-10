# streamlit_app.py
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Page config
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")

# Determine file paths relative to this script
base_dir = os.path.dirname(__file__)
csv_path = os.path.join(base_dir, 'california_infectious_diseases.csv')
geojson_path = os.path.join(base_dir, 'california-counties.geojson')

# File existence checks
if not os.path.exists(csv_path):
    st.error(f"CSV file not found at {csv_path}")
    st.stop()
if not os.path.exists(geojson_path):
    st.error(f"GeoJSON file not found at {geojson_path}")
    st.stop()

# Load data
df = pd.read_csv(csv_path)
with open(geojson_path) as f:
    counties_geo = json.load(f)

# Header
st.title("California Infectious Disease Dashboard")
st.markdown("_Data from 2001–2023 (Provisional)_")

# Sidebar filters
st.sidebar.header("Filters")
diseases = ['All Diseases'] + sorted(df['Disease'].unique())
counties = ['All Counties'] + sorted(df['County'].unique())
years = ['All Years'] + sorted(df['Year'].astype(str).unique())
sexes = ['All'] + sorted(df['Sex'].unique())

disease = st.sidebar.selectbox("Disease", diseases)
county = st.sidebar.selectbox("County", counties)
year = st.sidebar.selectbox("Year", years)
sex = st.sidebar.selectbox("Sex", sexes)

if st.sidebar.button("Clear Filters"):
    st.experimental_rerun()

# Filter dataframe
dff = df.copy()
if disease != 'All Diseases':
    dff = dff[dff['Disease'] == disease]
if county != 'All Counties':
    dff = dff[dff['County'] == county]
if year != 'All Years':
    dff = dff[dff['Year'] == int(year)]
if sex != 'All':
    dff = dff[dff['Sex'] == sex]

# Metrics cards
total = dff['Cases'].sum()
first = int(dff['Year'].min()) if not dff.empty else None
last = int(dff['Year'].max()) if not dff.empty else None
col1, col2, col3 = st.columns(3)
col1.metric("Total Cases", f"{total:,}")
col2.metric("First Reported Year", first)
col3.metric("Last Reported Year", last)

# Bar chart: Filtered Data Breakdown
bar_data = dff.groupby('Year')['Cases'].sum().reset_index()
fig_bar = px.bar(bar_data, x='Year', y='Cases', title='Filtered Data Breakdown')
fig_bar.update_layout(xaxis_title='Year', yaxis_title='Number of Cases')
st.plotly_chart(fig_bar, use_container_width=True)

# Map: Cases by County
map_data = dff.groupby('County')['Cases'].sum().reset_index()
fig_map = px.choropleth_mapbox(
    map_data, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
    color='Cases', hover_data=['County','Cases'],
    mapbox_style='carto-positron', zoom=5, center={'lat':37.5,'lon':-119.5}, opacity=0.6,
    title='Cases by County Map'
)
fig_map.update_layout(margin={'r':0,'t':30,'l':0,'b':0})
st.plotly_chart(fig_map, use_container_width=True)

# Line chart: Cases Over Time
line_data = bar_data.sort_values('Year')
fig_line = px.area(line_data, x='Year', y='Cases', title='Cases Over Time')
fig_line.update_layout(xaxis_title='Year', yaxis_title='Number of Cases')
st.plotly_chart(fig_line, use_container_width=True)
