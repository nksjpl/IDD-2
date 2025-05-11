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
      .dashboard-card {background-color: #ffffff; padding: 1rem; border-radius: 0.75rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom:1rem;}
      .metric-title {font-size: 0.9rem; color: #6b7280; margin-bottom: 0.25rem;}
      .metric-value {font-size: 1.75rem; color: #4e50ff; margin:0;}
      .section-header {font-size:1.5rem; font-weight:600; margin-top:1.5rem; margin-bottom:0.5rem;}
      body {background-color: #f3f4f6;}
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Helper: Color hashing ───────────────────────────────────────────────────
def string_to_color(name: str) -> str:
    h = 0
    for ch in name:
        h = ord(ch) + ((h << 5) - h)
        h &= 0xFFFFFFFF
    r = (h & 0xFF0000) >> 16
    g = (h & 0x00FF00) >> 8
    b = h & 0x0000FF
    if r > 100 and b > 100 and g < 100:
        g = (g + 128) % 256
    r = max(40, min(210, r))
    g = max(40, min(210, g))
    b = max(40, min(210, b))
    return f"#{r:02x}{g:02x}{b:02x}"

# ─── Data Loading ───────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
csv_path = os.path.join(BASE, 'california_infectious_diseases.csv')
geojson_path = os.path.join(BASE, 'california-counties.geojson')
if not os.path.exists(csv_path) or not os.path.exists(geojson_path):
    st.error("Data files missing. Make sure CSV and GeoJSON exist.")
    st.stop()
df = pd.read_csv(csv_path)
with open(geojson_path) as f:
    counties_geo = json.load(f)

# ─── Sidebar Filters ─────────────────────────────────────────────────────────
st.sidebar.header("Filters")
defaults = {'disease':'All Diseases', 'county':'All Counties', 'year':'All Years', 'sex':'All'}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val
options = {
    'disease': ['All Diseases'] + sorted(df['Disease'].unique()),
    'county':  ['All Counties'] + sorted(df['County'].unique()),
    'year':    ['All Years'] + sorted(df['Year'].astype(str).unique()),
    'sex':     ['All'] + sorted(df['Sex'].unique())
}
st.session_state['disease'] = st.sidebar.selectbox("Disease", options['disease'], index=options['disease'].index(st.session_state['disease']))
st.session_state['county']  = st.sidebar.selectbox("County",  options['county'],  index=options['county'].index(st.session_state['county']))
st.session_state['year']    = st.sidebar.selectbox("Year",    options['year'],    index=options['year'].index(st.session_state['year']))
st.session_state['sex']     = st.sidebar.selectbox("Sex",     options['sex'],     index=options['sex'].index(st.session_state['sex']))
if st.sidebar.button("Clear Filters"):
    for k, v in defaults.items():
        st.session_state[k] = v
    st.experimental_rerun()

# ─── Main Title ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>California Infectious Disease Dashboard</div>", unsafe_allow_html=True)
st.markdown("*Data from 2001–2023 (Provisional)*")

# ─── Apply Filters ──────────────────────────────────────────────────────────
df_filtered = df.copy()
if st.session_state['disease'] != defaults['disease']:
    df_filtered = df_filtered[df_filtered['Disease'] == st.session_state['disease']]
if st.session_state['county']  != defaults['county']:
    df_filtered = df_filtered[df_filtered['County']  == st.session_state['county']]
if st.session_state['year']    != defaults['year']:
    df_filtered = df_filtered[df_filtered['Year'] == int(st.session_state['year'])]
if st.session_state['sex']     != defaults['sex']:
    df_filtered = df_filtered[df_filtered['Sex'] == st.session_state['sex']]

# ─── Summary Metrics ───────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3, gap='medium')
total_cases = df_filtered['Cases'].sum()
first_year  = int(df_filtered['Year'].min()) if not df_filtered.empty else 'N/A'
last_year   = int(df_filtered['Year'].max()) if not df_filtered.empty else 'N/A'
with col1:
    st.markdown(f"<div class='dashboard-card'><p class='metric-title'>Total Cases</p><p class='metric-value'>{total_cases:,}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='dashboard-card'><p class='metric-title'>First Reported Year</p><p class='metric-value'>{first_year}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='dashboard-card'><p class='metric-title'>Last Reported Year</p><p class='metric-value'>{last_year}</p></div>", unsafe_allow_html=True)

# ─── Charts Layout ─────────────────────────────────────────────────────────
chart_left, chart_right = st.columns([2,1], gap='large')

# Bar Chart
bar_df = df_filtered.groupby('Year')['Cases'].sum().reset_index()
fig_bar = px.bar(bar_df, x='Year', y='Cases', labels={'Cases':'Cases'}, template='plotly_white', title='Filtered Data Breakdown')
with chart_left:
    st.plotly_chart(fig_bar, use_container_width=True)

# Map Chart with string-based colors and highlight
map_df = df_filtered.groupby('County', as_index=False)['Cases'].sum()
map_df['County'] = map_df['County'].str.title()

# Generate base colors
color_map = {row['County']: string_to_color(row['County']) for _, row in map_df.iterrows()}
# Highlight selected county in purple
selected = st.session_state['county']
if selected != defaults['county']:
    sel_title = selected.title()
    if sel_title in color_map:
        color_map[sel_title] = '#805AD5'

fig_map = px.choropleth_mapbox(
    map_df,
    geojson=counties_geo,
    locations='County',
    featureidkey='properties.NAME',
    color='County',
    color_discrete_map=color_map,
    hover_data=['County','Cases'],
    mapbox_style='carto-positron',
    center={'lat':37.5, 'lon':-119.5},
    zoom=5,
    opacity=0.8
)
fig_map.update_layout(margin={'r':0,'t':30,'l':0,'b':0}, showlegend=False)
with chart_right:
    st.plotly_chart(fig_map, use_container_width=True)

# Line Chart
st.markdown("<div class='section-header'>Cases Over Time</div>", unsafe_allow_html=True)
fig_line = px.area(bar_df, x='Year', y='Cases', labels={'Cases':'Cases'}, template='plotly_white')
st.plotly_chart(fig_line, use_container_width=True)
