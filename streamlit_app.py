# streamlit_app.py
import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# ─── Page Configuration & Styling ──────────────────────────────────────────
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")

# Custom CSS to style the app closer to the image
st.markdown(
"""
   <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .metric-card {background-color:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);text-align:center;}
      .metric-label{font-size:0.9rem;color:#6b7280;margin:0;}
      .metric-value{font-size:1.5rem;color:#4e50ff;margin:4px 0 0 0;}
      .section-title{font-size:1.25rem;margin:10px 0;font-weight:600;}
        /* Main app background */
        .main .block-container {
            padding-top: 2rem; /* Add some space at the top */
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Header styling */
        .header-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }
        .header-subtitle {
            text-align: center;
            font-size: 1rem;
            color: gray;
            margin-bottom: 2rem;
        }

        /* Filter section styling */
        .filter-container {
            background-color: #f0f2f5; /* Light gray background like in the image */
            padding: 20px;
            border-radius: 8px; /* Rounded corners */
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }
        .filter-container .stSelectbox label {
            font-weight: bold; /* Make filter labels bold */
        }

        /* Clear Filters button styling */
        /* We'll use Streamlit's button and try to style it, or use HTML for more control if needed */
        /* For precise styling, especially the red button, direct HTML/CSS via st.markdown might be better if Streamlit's button is limiting */

        /* Metric card styling */
        .metric-card-container {
            display: flex;
            justify-content: space-between;
            gap: 1rem; /* Spacing between cards */
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
            flex-grow: 1; /* Make cards take equal space */
        }
        .metric-label {
            font-size: 0.9rem;
            color: #6b7280; /* Gray color for label */
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 2rem; /* Larger font for value */
            color: #4A90E2; /* Blueish color for value, adjust as needed */
            font-weight: bold;
            margin: 0;
        }

        /* Chart titles */
        .chart-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            text-align: left;
        }

        /* Hide Streamlit's default hamburger menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Styling for the clear filters button to make it red */
        /* This targets a button with a specific key or class if possible */
        /* A more robust way for complex styling is to use st.markdown with HTML for the button */
        div.stButton > button {
            /* This is a general button style, can be made more specific */
        }

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
@st.cache_data
def load_data():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, 'california_infectious_diseases.csv')
    geojson_path = os.path.join(base_dir, 'california-counties.geojson')

    if not (os.path.exists(csv_path) and os.path.exists(geojson_path)):
        st.error("Data files (california_infectious_diseases.csv or california-counties.geojson) not found. Please ensure they are in the same directory as the app.")
        st.stop()

    df = pd.read_csv(csv_path)
    with open(geojson_path) as f:
        counties_geo = json.load(f)
    return df, counties_geo

df, counties_geo = load_data()

# Determine the correct GeoJSON feature key (NAME or name)
geojson_feature_key = 'properties.NAME' # Default
if counties_geo and 'features' in counties_geo and counties_geo['features']:
    properties = counties_geo['features'][0].get('properties', {})
    if 'name' in properties and 'NAME' not in properties:
        geojson_feature_key = 'properties.name'


# ─── Filter Options & Session State Initialization ─────────────────────────
DISEASES = ['All Diseases'] + sorted(df['Disease'].unique())
COUNTIES = ['All Counties'] + sorted(df['County'].unique())
YEARS = ['All Years'] + sorted(df['Year'].astype(str).unique())
SEXES = ['All'] + sorted(df['Sex'].unique())

# Initialize session state for filters if not already set
if 'disease_filter' not in st.session_state:
    st.session_state.disease_filter = 'All Diseases'
if 'county_filter' not in st.session_state:
    st.session_state.county_filter = 'All Counties'
if 'year_filter' not in st.session_state:
    st.session_state.year_filter = 'All Years'
if 'sex_filter' not in st.session_state:
    st.session_state.sex_filter = 'All'

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
st.markdown("<div class='header-title'>California Infectious Disease Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Data from 2001–2023 (Provisional)</div>", unsafe_allow_html=True)

# ─── Filter Section ─────────────────────────────────────────────────────────
st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
st.subheader("Filters") # Adding a "Filters" subheader as in the image

filter_cols = st.columns([3, 3, 3, 3, 2]) # 4 for dropdowns, 1 for button

with filter_cols[0]:
    sel_disease = st.selectbox(
        "Disease",
        DISEASES,
        key='disease_filter_widget', # Use a different key for widget if session_state key is used for value
        index=DISEASES.index(st.session_state.disease_filter)
    )
    st.session_state.disease_filter = sel_disease # Update session state

with filter_cols[1]:
    sel_county = st.selectbox(
        "County",
        COUNTIES,
        key='county_filter_widget',
        index=COUNTIES.index(st.session_state.county_filter)
    )
    st.session_state.county_filter = sel_county

with filter_cols[2]:
    sel_year = st.selectbox(
        "Year",
        YEARS,
        key='year_filter_widget',
        index=YEARS.index(st.session_state.year_filter)
    )
    st.session_state.year_filter = sel_year

with filter_cols[3]:
    sel_sex = st.selectbox(
        "Sex",
        SEXES,
        key='sex_filter_widget',
        index=SEXES.index(st.session_state.sex_filter)
    )
    st.session_state.sex_filter = sel_sex

with filter_cols[4]:
    st.write("") # Spacer for alignment
    st.write("") # Spacer for alignment
    if st.button("Clear Filters", key="clear_filters_button", help="Reset all filters to default values"):
        st.session_state.disease_filter = 'All Diseases'
        st.session_state.county_filter = 'All Counties'
        st.session_state.year_filter = 'All Years'
        st.session_state.sex_filter = 'All'
        # Need to re-assign widget values after state change for immediate update
        st.experimental_rerun() # Rerun to reflect cleared filters

st.markdown("</div>", unsafe_allow_html=True) # Close filter-container

# Apply CSS for the red button using markdown (more reliable for specific styling)
st.markdown("""
<style>
    /* Targeting the button specifically by a part of its Streamlit-generated ID or class */
    /* This is tricky and might need adjustment based on Streamlit's HTML structure */
    /* A more robust way is to give the button a unique class if Streamlit allows or wrap it */
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) .stButton button {
        background-color: #FF4B4B !important; /* Red color */
        color: white !important;
        border-radius: 4px !important;
        border: none !important;
        padding: 0.4rem 1rem !important; /* Adjust padding */
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) .stButton button:hover {
        background-color: #E04040 !important; /* Darker red on hover */
    }
</style>
""", unsafe_allow_html=True)


# ─── Apply Filters to Data ──────────────────────────────────────────────────
df_filtered = df.copy()
if st.session_state.disease_filter != 'All Diseases':
    df_filtered = df_filtered[df_filtered['Disease'] == st.session_state.disease_filter]
if st.session_state.county_filter != 'All Counties':
    df_filtered = df_filtered[df_filtered['County'] == st.session_state.county_filter]
if st.session_state.year_filter != 'All Years':
    df_filtered = df_filtered[df_filtered['Year'] == int(st.session_state.year_filter)]
if st.session_state.sex_filter != 'All':
    df_filtered = df_filtered[df_filtered['Sex'] == st.session_state.sex_filter]

# ─── Metrics Cards ───────────────────────────────────────────────────────────
st.markdown("<div class='metric-card-container'>", unsafe_allow_html=True)

total_cases = int(df_filtered['Cases'].sum())
first_reported_year = df_filtered['Year'].min() if not df_filtered.empty else "N/A"
last_reported_year = df_filtered['Year'].max() if not df_filtered.empty else "N/A"

# Card 1: Total Cases
st.markdown(f"""
<div class='metric-card'>
    <p class='metric-label'>Total Cases</p>
    <p class='metric-value'>{total_cases:,}</p>
</div>
""", unsafe_allow_html=True)

# Card 2: First Reported Year
st.markdown(f"""
<div class='metric-card'>
    <p class='metric-label'>First Reported Year</p>
    <p class='metric-value'>{first_reported_year}</p>
</div>
""", unsafe_allow_html=True)

# Card 3: Last Reported Year
st.markdown(f"""
<div class='metric-card'>
    <p class='metric-label'>Last Reported Year</p>
    <p class='metric-value'>{last_reported_year}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# ─── Charts Section ─────────────────────────────────────────────────────────
charts_col1, charts_col2 = st.columns([0.65, 0.35], gap="large") # As per image, bar chart is wider

with charts_col1:
    st.markdown("<div class='chart-title'>Filtered Data Breakdown</div>", unsafe_allow_html=True)
    bar_data = df_filtered.groupby('Year')['Cases'].sum().reset_index()
    fig_bar = px.bar(
        bar_data,
        x='Year',
        y='Cases',
        labels={'Cases': 'Number of Cases', 'Year': 'Year'},
        template='plotly_white'
    )
    fig_bar.update_layout(
        margin=dict(t=30, l=60, r=20, b=40), # Adjusted margins
        yaxis_title="Number of Cases",
        xaxis_title="Year"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with charts_col2:
    st.markdown("<div class='chart-title'>Cases by County Map</div>", unsafe_allow_html=True)
    map_data = df_filtered.groupby('County')['Cases'].sum().reset_index()
    map_data['County'] = map_data['County'].str.title() # Ensure consistent casing with GeoJSON

    fig_map = px.choropleth_mapbox(
        map_data,
        geojson=counties_geo,
        locations='County',
        featureidkey=geojson_feature_key, # Use determined key
        color='Cases',
        color_continuous_scale="Viridis", # Or another sequential scale like "Plasma", "Blues"
        range_color=(0, map_data['Cases'].max() if not map_data.empty else 1), # Dynamic range
        mapbox_style='carto-positron',
        center={'lat': 37.5, 'lon': -119.5},
        zoom=4.5, # Adjusted zoom
        opacity=0.7, # Adjusted opacity
        hover_data={'County': True, 'Cases': True}
    )
    fig_map.update_layout(
        margin=dict(t=30, l=0, r=0, b=0),
        coloraxis_colorbar=dict(title="Cases")
    )
    st.plotly_chart(fig_map, use_container_width=True)

# Cases Over Time (Line Chart) - Full Width
st.markdown("<div class='chart-title' style='margin-top: 2rem;'>Cases Over Time</div>", unsafe_allow_html=True)
# Data for line chart is the same as bar chart's aggregated data
line_data = bar_data.copy() # Re-use bar_data if appropriate or re-aggregate if needed
fig_line = px.area( # Using area chart as in the image
    line_data,
    x='Year',
    y='Cases',
    labels={'Cases': 'Number of Cases', 'Year': 'Year'},
template='plotly_white'
)
fig_map.update_layout(showlegend=False)
map_col.plotly_chart(fig_map, use_container_width=True)
fig_line.update_layout(
    margin=dict(t=30, l=60, r=20, b=40), # Adjusted margins
    yaxis_title="Number of Cases",
    xaxis_title="Year"
)
fig_line.update_traces(fillcolor='rgba(74,144,226,0.3)', line=dict(color='rgba(74,144,226,1)')) # Example fill and line color

# Line chart
st.markdown("<div class='section-title'>Cases Over Time</div>", unsafe_allow_html=True)
fig_line = px.area(bar_df, x='Year', y='Cases', template='plotly_white', labels={'Cases': 'Number of Cases'})
st.plotly_chart(fig_line, use_container_width=True)

# Add a note about data files if they were not found initially by load_data
if not os.path.exists(os.path.join(os.path.dirname(__file__), 'california_infectious_diseases.csv')):
    st.warning("Reminder: `california_infectious_diseases.csv` and `california-counties.geojson` must be in the same directory as this script.")
