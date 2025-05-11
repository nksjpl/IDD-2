# streamlit_app.py
import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# ─── Page Configuration & Styling ──────────────────────────────────────────
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .metric-card {background-color:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);text-align:center;}
      .metric-label{font-size:0.9rem;color:#6b7280;margin:0;}
      .metric-value{font-size:1.5rem;color:#4e50ff;margin:4px 0 0 0;}
      .section-title{font-size:1.25rem;margin:10px 0;font-weight:600;}
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Data Loading ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
CSV = os.path.join(BASE_DIR, 'california_infectious_diseases.csv')
GEO = os.path.join(BASE_DIR, 'california-counties.geojson')
if not (os.path.exists(CSV) and os.path.exists(GEO)):
    st.error("CSV or GeoJSON missing in app directory.")
    st.stop()

df = pd.read_csv(CSV)
with open(GEO) as f:
    counties_geo = json.load(f)

# ─── Utility: deterministic color per county ───────────────────────────────
def string_to_color(name: str) -> str:
    h = 0
    for ch in name:
        h = (h << 5) - h + ord(ch)
    r = (h & 0xFF0000) >> 16
    g = (h & 0x00FF00) >> 8
    b = h & 0x0000FF
    r = 40 + (r % 180)  # keep within 40‑220 to avoid too dark/light
    g = 40 + (g % 180)
    b = 40 + (b % 180)
    return f"#{r:02x}{g:02x}{b:02x}"

# ─── Sidebar Filters ────────────────────────────────────────────────────────
st.sidebar.header("Filters")
DEFAULTS = {'disease': 'All Diseases', 'county': 'All Counties', 'year': 'All Years', 'sex': 'All'}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

opts_disease = ['All Diseases'] + sorted(df['Disease'].unique())
opts_county  = ['All Counties'] + sorted(df['County'].unique())
opts_year    = ['All Years'] + sorted(df['Year'].astype(str).unique())
opts_sex     = ['All'] + sorted(df['Sex'].unique())

sel_disease = st.sidebar.selectbox("Disease", opts_disease, index=opts_disease.index(st.session_state['disease']), key='disease')
sel_county  = st.sidebar.selectbox("County",  opts_county,  index=opts_county.index(st.session_state['county']),  key='county')
sel_year    = st.sidebar.selectbox("Year",    opts_year,    index=opts_year.index(st.session_state['year']),    key='year')
sel_sex     = st.sidebar.selectbox("Sex",     opts_sex,     index=opts_sex.index(st.session_state['sex']),     key='sex')

# ─── Header ─────────────────────────────────────────────────────────────────
st.title("California Infectious Disease Dashboard")
st.caption("Data from 2001–2023 (Provisional)")

# ─── Apply Filters ──────────────────────────────────────────────────────────
filtered = df.copy()
if sel_disease != 'All Diseases':
    filtered = filtered[filtered['Disease'] == sel_disease]
if sel_county != 'All Counties':
    filtered = filtered[filtered['County'] == sel_county]
if sel_year != 'All Years':
    filtered = filtered[filtered['Year'] == int(sel_year)]
if sel_sex != 'All':
    filtered = filtered[filtered['Sex'] == sel_sex]

# ─── Metrics ───────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3, gap="large")

total = int(filtered['Cases'].sum())
first = int(filtered['Year'].min()) if not filtered.empty else 'N/A'
last  = int(filtered['Year'].max()) if not filtered.empty else 'N/A'

with col1:
    st.markdown(f"<div class='metric-card'><p class='metric-label'>Total Cases</p><p class='metric-value'>{total:,}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'><p class='metric-label'>First Reported Year</p><p class='metric-value'>{first}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><p class='metric-label'>Last Reported Year</p><p class='metric-value'>{last}</p></div>", unsafe_allow_html=True)

# ─── Charts ────────────────────────────────────────────────────────────────
bar_col, map_col = st.columns([2, 1], gap="large")

# Bar chart
bar_df = filtered.groupby('Year')['Cases'].sum().reset_index()
fig_bar = px.bar(bar_df, x='Year', y='Cases', title='Filtered Data Breakdown', template='plotly_white', labels={'Cases': 'Number of Cases'})
bar_col.plotly_chart(fig_bar, use_container_width=True)

# Map chart with unique colors per county
map_df = filtered.groupby('County', as_index=False)['Cases'].sum()
map_df['County'] = map_df['County'].str.title()

# Build deterministic color map for all counties (handle NAME vs name keys)
try:
    all_counties = {feat['properties']['NAME'].title() for feat in counties_geo['features']}
    feature_key = 'properties.NAME'
except KeyError:
    all_counties = {feat['properties']['name'].title() for feat in counties_geo['features']}
    feature_key = 'properties.name'

color_map = {county: string_to_color(county) for county in all_counties}

fig_map = px.choropleth_mapbox(
    map_df,
    geojson=counties_geo,
    locations='County',
    featureidkey=feature_key,
    color='County',
    color_discrete_map=color_map,
    hover_data=['County','Cases'],
    mapbox_style='carto-positron',
    center={'lat':37.5,'lon':-119.5},
    zoom=5,
    opacity=0.85,
    title='Cases by County Map',
    template='plotly_white'
)
 px.choropleth_mapbox(
    map_df,
    geojson=counties_geo,
    locations='County',
    featureidkey='properties.NAME',
    color='County',  # use county name for discrete colors
    color_discrete_map=color_map,
    hover_data=['County', 'Cases'],
    mapbox_style='carto-positron',
    center={'lat': 37.5, 'lon': -119.5},
    zoom=5,
    opacity=0.85,
    title='Cases by County Map',
    template='plotly_white'
)
fig_map.update_layout(showlegend=False)
map_col.plotly_chart(fig_map, use_container_width=True)

# Line chart
st.markdown("<div class='section-title'>Cases Over Time</div>", unsafe_allow_html=True)
fig_line = px.area(bar_df, x='Year', y='Cases', template='plotly_white', labels={'Cases': 'Number of Cases'})
st.plotly_chart(fig_line, use_container_width=True)
