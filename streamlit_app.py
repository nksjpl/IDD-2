# streamlit_app.py
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import json

# ─── Page Configuration & Global Styles ──────────────────────────────────────
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")
# Hide default Streamlit header/menu/footer
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .card {background-color: #ffffff; padding: 1rem; border-radius: 0.75rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
      .filter-container {background-color: #ffffff; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1.5rem;}
      .section-title {font-size: 1.5rem; margin-bottom: 0.5rem; font-weight: 600;}
      body {background-color: #f3f4f6;}
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Data Loading ────────────────────────────────────────────────────────────
base_dir = os.path.dirname(__file__)
csv_path = os.path.join(base_dir, 'california_infectious_diseases.csv')
geojson_path = os.path.join(base_dir, 'california-counties.geojson')

if not os.path.exists(csv_path):
    st.error(f"❌ CSV file not found at {csv_path}")
    st.stop()
if not os.path.exists(geojson_path):
    st.error(f"❌ GeoJSON file not found at {geojson_path}")
    st.stop()

df = pd.read_csv(csv_path)
with open(geojson_path) as f:
    counties_geo = json.load(f)

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("# California Infectious Disease Dashboard")
st.markdown("*Data from 2001–2023 (Provisional)*")

# ─── Filters Section ─────────────────────────────────────────────────────────
st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Filters</div>", unsafe_allow_html=True)
cols = st.columns([1,1,1,1,0.5], gap='small')

diseases = ['All Diseases'] + sorted(df['Disease'].unique())
counties = ['All Counties'] + sorted(df['County'].unique())
years = ['All Years'] + sorted(df['Year'].astype(str).unique())
sexes = ['All'] + sorted(df['Sex'].unique())

with cols[0]:
    disease = st.selectbox("Disease", diseases, key='disease')
with cols[1]:
    county = st.selectbox("County", counties, key='county')
with cols[2]:
    year = st.selectbox("Year", years, key='year')
with cols[3]:
    sex = st.selectbox("Sex", sexes, key='sex')
with cols[4]:
    st.markdown("<br>", unsafe_allow_html=True)  # Align button
    if st.button("Clear Filters", key='clear_filters'):
        for k, v in {'disease':'All Diseases','county':'All Counties','year':'All Years','sex':'All'}.items():
            st.session_state[k] = v
        st.experimental_rerun()
st.markdown("</div>", unsafe_allow_html=True)

# Build filtered DataFrame
filtered = df.copy()
if disease != 'All Diseases': filtered = filtered[filtered['Disease'] == disease]
if county != 'All Counties': filtered = filtered[filtered['County'] == county]
if year != 'All Years':    filtered = filtered[filtered['Year'] == int(year)]
if sex != 'All':           filtered = filtered[filtered['Sex'] == sex]

# ─── Summary Cards ──────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Summary Statistics</div>", unsafe_allow_html=True)
card_cols = st.columns(3, gap='medium')

total_cases = int(filtered['Cases'].sum())
first_year = int(filtered['Year'].min()) if not filtered.empty else 'N/A'
last_year  = int(filtered['Year'].max()) if not filtered.empty else 'N/A'

with card_cols[0]:
    st.markdown(
        f"<div class='card'><h4>Total Cases</h4><h2 style='color:#4e50ff'>{total_cases:,}</h2></div>",
        unsafe_allow_html=True
    )
with card_cols[1]:
    st.markdown(
        f"<div class='card'><h4>First Reported Year</h4><h2 style='color:#4e50ff'>{first_year}</h2></div>",
        unsafe_allow_html=True
    )
with card_cols[2]:
    st.markdown(
        f"<div class='card'><h4>Last Reported Year</h4><h2 style='color:#4e50ff'>{last_year}</h2></div>",
        unsafe_allow_html=True
    )

# ─── Charts ──────────────────────────────────────────────────────────────────
chart_cols = st.columns([2, 1], gap='large')

# Bar Chart
bar_data = filtered.groupby('Year')['Cases'].sum().reset_index()
fig_bar = px.bar(bar_data, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, title='Filtered Data Breakdown', template='plotly_white')

# Map
map_data = filtered.groupby('County')['Cases'].sum().reset_index()
fig_map = px.choropleth_mapbox(
    map_data, geojson=counties_geo, locations='County', featureidkey='properties.NAME',
    color='Cases', hover_data=['County','Cases'], mapbox_style='carto-positron',
    zoom=5, center={'lat':37.5,'lon':-119.5}, opacity=0.6, title='Cases by County Map', template='plotly_white'
)
fig_map.update_layout(margin={'r':0,'t':30,'l':0,'b':0})

with chart_cols[0]:
    st.plotly_chart(fig_bar, use_container_width=True)
with chart_cols[1]:
    st.plotly_chart(fig_map, use_container_width=True)

# Line Chart
st.markdown("<div class='section-title'>Cases Over Time</div>", unsafe_allow_html=True)
fig_line = px.area(bar_data, x='Year', y='Cases', labels={'Cases':'Number of Cases'}, template='plotly_white')
st.plotly_chart(fig_line, use_container_width=True)
