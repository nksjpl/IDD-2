# streamlit_app.py
import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# ─── Page Configuration & Styling ──────────────────────────────────────────
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Google-inspired color palette
PRIMARY_COLOR = "#1a73e8" # Google Blue
SECONDARY_COLOR = "#5f6368" # Google Grey for text
BACKGROUND_COLOR = "#f8f9fa" # Very light grey for page background
CARD_BACKGROUND_COLOR = "#ffffff" # White for cards
ACCENT_RED = "#ea4335" # Google Red
ACCENT_GREEN = "#34a853" # Google Green
ACCENT_YELLOW = "#fbbc05" # Google Yellow

# Custom CSS for a more professional "Google-like" finish
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

        body {{
            font-family: 'Open Sans', sans-serif;
            background-color: {BACKGROUND_COLOR};
            color: {SECONDARY_COLOR};
        }}

        /* Main app container */
        .main .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }}

        /* Header styling */
        .header-title {{
            text-align: center;
            font-family: 'Roboto', sans-serif;
            font-size: 2.8rem;
            font-weight: 700;
            color: #202124; /* Darker grey for main title */
            margin-bottom: 0.3rem;
        }}
        .header-subtitle {{
            text-align: center;
            font-family: 'Roboto', sans-serif;
            font-size: 1.1rem;
            color: {SECONDARY_COLOR};
            margin-bottom: 2.5rem;
            font-weight: 300;
        }}

        /* Filter section styling */
        .filter-container {{
            background-color: {CARD_BACKGROUND_COLOR};
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 2.5rem;
        }}
        .filter-container .stSelectbox label {{
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            color: #3c4043;
            font-size: 0.95rem;
        }}
        .filter-container .stButton button {{
            background-color: {ACCENT_RED} !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.55rem 1.2rem !important;
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            width: 100%;
            transition: background-color 0.2s ease;
        }}
        .filter-container .stButton button:hover {{
            background-color: #d0382b !important;
        }}
         .filter-container .stButton button:active {{
            background-color: #b02d23 !important;
        }}
        .filter-container h3 {{ /* Subheader "Filters" */
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            color: #202124;
            margin-top: 0;
            margin-bottom: 1.5rem;
            font-size: 1.6rem;
        }}


        /* Metric card styling */
        .metric-card-container {{
            display: grid; /* Using grid for better responsiveness */
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .metric-card {{
            background-color: {CARD_BACKGROUND_COLOR};
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.12);
        }}
        .metric-label {{
            font-family: 'Roboto', sans-serif;
            font-size: 1rem;
            color: {SECONDARY_COLOR};
            margin-bottom: 0.5rem;
            font-weight: 400;
        }}
        .metric-value {{
            font-family: 'Roboto', sans-serif;
            font-size: 2.6rem;
            color: {PRIMARY_COLOR};
            font-weight: 700;
            margin: 0;
        }}
        .metric-icon {{ /* Placeholder for potential future icons */
            font-size: 1.8rem;
            color: {PRIMARY_COLOR};
            margin-bottom: 0.5rem;
        }}


        /* Chart titles */
        .chart-title {{
            font-family: 'Roboto', sans-serif;
            font-size: 1.4rem;
            font-weight: 500;
            color: #202124;
            margin-bottom: 1rem;
            text-align: left;
        }}

        /* General Plotly chart styling */
        .stPlotlyChart {{
            border-radius: 12px;
            overflow: hidden; /* Ensures chart respects border radius */
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}


        /* Hide Streamlit's default hamburger menu and footer */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

    </style>
    """,
    unsafe_allow_html=True
)

# ─── Data Loading ───────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, 'california_infectious_diseases.csv')
    geojson_path = os.path.join(base_dir, 'california-counties.geojson')

    if not (os.path.exists(csv_path) and os.path.exists(geojson_path)):
        st.error("Data files (california_infectious_diseases.csv or california-counties.geojson) not found. "
                 "Please ensure they are in the same directory as the app.")
        st.stop()

    df = pd.read_csv(csv_path)
    with open(geojson_path) as f:
        counties_geo = json.load(f)
    return df, counties_geo

df, counties_geo = load_data()

geojson_feature_key = 'properties.NAME'
if counties_geo and 'features' in counties_geo and counties_geo['features']:
    properties = counties_geo['features'][0].get('properties', {})
    if 'name' in properties and 'NAME' not in properties:
        geojson_feature_key = 'properties.name'


# ─── Filter Options & Session State Initialization ─────────────────────────
DISEASES = ['All Diseases'] + sorted(df['Disease'].unique())
COUNTIES = ['All Counties'] + sorted(df['County'].unique())
YEARS = ['All Years'] + sorted(df['Year'].astype(str).unique())
SEXES = ['All'] + sorted(df['Sex'].unique())

if 'disease_filter' not in st.session_state:
    st.session_state.disease_filter = 'All Diseases'
if 'county_filter' not in st.session_state:
    st.session_state.county_filter = 'All Counties'
if 'year_filter' not in st.session_state:
    st.session_state.year_filter = 'All Years'
if 'sex_filter' not in st.session_state:
    st.session_state.sex_filter = 'All'

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("<div class='header-title'>California Infectious Disease Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Interactive Data from 2001–2023 (Provisional)</div>", unsafe_allow_html=True)

# ─── Filter Section ─────────────────────────────────────────────────────────
st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
st.subheader("Filters")

filter_cols = st.columns([3, 3, 3, 3, 2])

with filter_cols[0]:
    sel_disease = st.selectbox(
        "Disease", DISEASES, key='disease_filter_widget',
        index=DISEASES.index(st.session_state.disease_filter)
    )
    if st.session_state.disease_filter != sel_disease:
        st.session_state.disease_filter = sel_disease
        st.rerun()

with filter_cols[1]:
    sel_county = st.selectbox(
        "County", COUNTIES, key='county_filter_widget',
        index=COUNTIES.index(st.session_state.county_filter)
    )
    if st.session_state.county_filter != sel_county:
        st.session_state.county_filter = sel_county
        st.rerun()

with filter_cols[2]:
    sel_year = st.selectbox(
        "Year", YEARS, key='year_filter_widget',
        index=YEARS.index(st.session_state.year_filter)
    )
    if st.session_state.year_filter != sel_year:
        st.session_state.year_filter = sel_year
        st.rerun()

with filter_cols[3]:
    sel_sex = st.selectbox(
        "Sex", SEXES, key='sex_filter_widget',
        index=SEXES.index(st.session_state.sex_filter)
    )
    if st.session_state.sex_filter != sel_sex:
        st.session_state.sex_filter = sel_sex
        st.rerun()

with filter_cols[4]:
    st.write("") 
    st.write("") 
    if st.button("Clear Filters", key="clear_filters_button", help="Reset all filters to default values"):
        st.session_state.disease_filter = 'All Diseases'
        st.session_state.county_filter = 'All Counties'
        st.session_state.year_filter = 'All Years'
        st.session_state.sex_filter = 'All'
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


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

# Unicode icons (examples)
ICON_CASES = "📊" # or "📈"
ICON_CALENDAR_START = "🗓️" # or "📅"
ICON_CALENDAR_END = "🗓️"

metric_cards_html = f"""
    <div class='metric-card'>
        <div class='metric-icon'>{ICON_CASES}</div>
        <p class='metric-label'>Total Cases</p>
        <p class='metric-value'>{total_cases:,}</p>
    </div>
    <div class='metric-card'>
        <div class='metric-icon'>{ICON_CALENDAR_START}</div>
        <p class='metric-label'>First Reported Year</p>
        <p class='metric-value'>{first_reported_year}</p>
    </div>
    <div class='metric-card'>
        <div class='metric-icon'>{ICON_CALENDAR_END}</div>
        <p class='metric-label'>Last Reported Year</p>
        <p class='metric-value'>{last_reported_year}</p>
    </div>
"""
st.markdown(metric_cards_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)


# ─── Charts Section ─────────────────────────────────────────────────────────
charts_col1, charts_col2 = st.columns([0.62, 0.38], gap="large") # Adjusted column ratio

# Plotly chart font and general layout settings
chart_layout_defaults = {
    'font': {'family': "Open Sans, sans-serif", 'size': 12, 'color': SECONDARY_COLOR},
    'title_font': {'family': "Roboto, sans-serif", 'size': 16, 'color': '#202124'},
    'paper_bgcolor': CARD_BACKGROUND_COLOR, # Match card background
    'plot_bgcolor': CARD_BACKGROUND_COLOR,  # Match card background
    'legend': {'font': {'size': 11}}
}

with charts_col1:
    st.markdown("<div class='chart-title'>Filtered Data Breakdown (by Year)</div>", unsafe_allow_html=True)
    bar_data = df_filtered.groupby('Year')['Cases'].sum().reset_index()
    fig_bar = px.bar(
        bar_data, x='Year', y='Cases',
        labels={'Cases': 'Number of Cases', 'Year': 'Year'},
        color_discrete_sequence=[PRIMARY_COLOR] # Use primary color for bars
    )
    fig_bar.update_layout(
        **chart_layout_defaults,
        margin=dict(t=50, l=70, r=30, b=50),
        yaxis_title="Number of Cases",
        xaxis_title="Year",
        bargap=0.2
    )
    fig_bar.update_traces(marker_line_width=0) # Remove border from bars
    st.plotly_chart(fig_bar, use_container_width=True)

with charts_col2:
    st.markdown("<div class='chart-title'>Cases by County Map</div>", unsafe_allow_html=True)
    map_data = df_filtered.groupby('County')['Cases'].sum().reset_index()
    map_data['County'] = map_data['County'].str.title()

    fig_map = px.choropleth_mapbox(
        map_data, geojson=counties_geo, locations='County',
        featureidkey=geojson_feature_key, color='Cases',
        color_continuous_scale=px.colors.sequential.Blues, # Google-friendly blue scale
        range_color=(0, map_data['Cases'].max() if not map_data.empty else 1),
        mapbox_style='carto-positron',
        center={'lat': 37.5, 'lon': -119.5}, zoom=4.7, opacity=0.75,
        hover_data={'County': True, 'Cases': ':,2f'} # Format hover cases
    )
    fig_map.update_layout(
        **chart_layout_defaults,
        margin=dict(t=50, l=0, r=0, b=0),
        coloraxis_colorbar=dict(
            title="Cases",
            tickfont={'family': "Open Sans", 'size': 10, 'color': SECONDARY_COLOR},
            titlefont={'family': "Roboto", 'size': 12, 'color': SECONDARY_COLOR}
        )
    )
    st.plotly_chart(fig_map, use_container_width=True)

st.markdown("<div class='chart-title' style='margin-top: 2.5rem;'>Cases Over Time (Trend)</div>", unsafe_allow_html=True)
line_data = df_filtered.groupby('Year')['Cases'].sum().reset_index() # Ensure it uses filtered data
fig_line = px.area(
    line_data, x='Year', y='Cases',
    labels={'Cases': 'Number of Cases', 'Year': 'Year'}
)
fig_line.update_layout(
    **chart_layout_defaults,
    margin=dict(t=50, l=70, r=30, b=50),
    yaxis_title="Number of Cases",
    xaxis_title="Year"
)
fig_line.update_traces(
    fillcolor=f'rgba({int(PRIMARY_COLOR[1:3], 16)}, {int(PRIMARY_COLOR[3:5], 16)}, {int(PRIMARY_COLOR[5:7], 16)}, 0.2)', # Lighter primary color fill
    line=dict(color=PRIMARY_COLOR, width=2.5)
)
st.plotly_chart(fig_line, use_container_width=True)

if not os.path.exists(os.path.join(os.path.dirname(__file__), 'california_infectious_diseases.csv')):
    st.caption("Reminder: `california_infectious_diseases.csv` and `california-counties.geojson` must be in the same directory as this script for the dashboard to function correctly.")

