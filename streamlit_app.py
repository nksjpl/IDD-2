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
        /* This targets the button within the specific column structure */
        div[data-testid="stHorizontalBlock"] > div:nth-child(5) .stButton button {
            background-color: #FF4B4B !important; /* Red color */
            color: white !important;
            border-radius: 4px !important;
            border: none !important;
            padding: 0.4rem 1rem !important; /* Adjust padding as needed */
            width: 100%; /* Make button take full width of its column */
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(5) .stButton button:hover {
            background-color: #E04040 !important; /* Darker red on hover */
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(5) .stButton button:active {
            background-color: #C03030 !important; /* Even darker red on click */
        }

    </style>
    """,
    unsafe_allow_html=True
)

# ─── Data Loading ───────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # Get the directory of the current script
    base_dir = os.path.dirname(__file__)
    # Define paths to the data files
    csv_path = os.path.join(base_dir, 'california_infectious_diseases.csv')
    geojson_path = os.path.join(base_dir, 'california-counties.geojson')

    # Check if data files exist
    if not (os.path.exists(csv_path) and os.path.exists(geojson_path)):
        st.error("Data files (california_infectious_diseases.csv or california-counties.geojson) not found. "
                 "Please ensure they are in the same directory as the app.")
        st.stop() # Stop execution if files are missing

    # Load the CSV data into a pandas DataFrame
    df = pd.read_csv(csv_path)
    # Load the GeoJSON data
    with open(geojson_path) as f:
        counties_geo = json.load(f)
    return df, counties_geo

df, counties_geo = load_data()

# Determine the correct GeoJSON feature key (e.g., 'properties.NAME' or 'properties.name')
geojson_feature_key = 'properties.NAME' # Default assumption
if counties_geo and 'features' in counties_geo and counties_geo['features']:
    # Check the properties of the first feature to find the county name key
    properties = counties_geo['features'][0].get('properties', {})
    if 'name' in properties and 'NAME' not in properties:
        geojson_feature_key = 'properties.name'


# ─── Filter Options & Session State Initialization ─────────────────────────
# Define options for filter dropdowns
DISEASES = ['All Diseases'] + sorted(df['Disease'].unique())
COUNTIES = ['All Counties'] + sorted(df['County'].unique())
YEARS = ['All Years'] + sorted(df['Year'].astype(str).unique())
SEXES = ['All'] + sorted(df['Sex'].unique())

# Initialize session state for filters if they are not already set
# This preserves filter selections across reruns
if 'disease_filter' not in st.session_state:
    st.session_state.disease_filter = 'All Diseases'
if 'county_filter' not in st.session_state:
    st.session_state.county_filter = 'All Counties'
if 'year_filter' not in st.session_state:
    st.session_state.year_filter = 'All Years'
if 'sex_filter' not in st.session_state:
    st.session_state.sex_filter = 'All'

# ─── Header ─────────────────────────────────────────────────────────────────
# Display the main title and subtitle of the dashboard
st.markdown("<div class='header-title'>California Infectious Disease Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Data from 2001–2023 (Provisional)</div>", unsafe_allow_html=True)

# ─── Filter Section ─────────────────────────────────────────────────────────
# Create a container for the filters
st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
st.subheader("Filters") # Section title for filters

# Arrange filters in columns: 4 for dropdowns, 1 for the clear button
filter_cols = st.columns([3, 3, 3, 3, 2]) # Relative widths of columns

# Disease Filter
with filter_cols[0]:
    # Create a selectbox for disease selection
    # The index is set based on the current session state value
    sel_disease = st.selectbox(
        "Disease",
        DISEASES,
        key='disease_filter_widget', # Unique key for the widget
        index=DISEASES.index(st.session_state.disease_filter)
    )
    # Update the session state when the selection changes
    if st.session_state.disease_filter != sel_disease:
        st.session_state.disease_filter = sel_disease
        st.rerun() # Rerun the app to apply the filter

# County Filter
with filter_cols[1]:
    sel_county = st.selectbox(
        "County",
        COUNTIES,
        key='county_filter_widget',
        index=COUNTIES.index(st.session_state.county_filter)
    )
    if st.session_state.county_filter != sel_county:
        st.session_state.county_filter = sel_county
        st.rerun()

# Year Filter
with filter_cols[2]:
    sel_year = st.selectbox(
        "Year",
        YEARS,
        key='year_filter_widget',
        index=YEARS.index(st.session_state.year_filter)
    )
    if st.session_state.year_filter != sel_year:
        st.session_state.year_filter = sel_year
        st.rerun()

# Sex Filter
with filter_cols[3]:
    sel_sex = st.selectbox(
        "Sex",
        SEXES,
        key='sex_filter_widget',
        index=SEXES.index(st.session_state.sex_filter)
    )
    if st.session_state.sex_filter != sel_sex:
        st.session_state.sex_filter = sel_sex
        st.rerun()

# Clear Filters Button
with filter_cols[4]:
    st.write("") # Add a small vertical spacer for alignment with selectbox labels
    st.write("") # Add a small vertical spacer for alignment
    if st.button("Clear Filters", key="clear_filters_button", help="Reset all filters to default values"):
        # Reset all filter values in session state
        st.session_state.disease_filter = 'All Diseases'
        st.session_state.county_filter = 'All Counties'
        st.session_state.year_filter = 'All Years'
        st.session_state.sex_filter = 'All'
        st.rerun() # Rerun the app to reflect the cleared filters

st.markdown("</div>", unsafe_allow_html=True) # Close filter-container


# ─── Apply Filters to Data ──────────────────────────────────────────────────
# Create a filtered DataFrame based on current selections
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
# Wrapper div for bottom margin, replacing .metric-card-container's margin role
st.markdown("<div style='margin-bottom: 2.5rem;'>", unsafe_allow_html=True)

metric_cols = st.columns(3, gap="large") # Use st.columns for horizontal layout

total_cases = int(df_filtered['Cases'].sum())
first_reported_year = df_filtered['Year'].min() if not df_filtered.empty else "N/A"
last_reported_year = df_filtered['Year'].max() if not df_filtered.empty else "N/A"

ICON_CASES = "📊"
ICON_CALENDAR_START = "🗓️"
ICON_CALENDAR_END = "🗓️"

with metric_cols[0]:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-icon'>{ICON_CASES}</div>
        <p class='metric-label'>Total Cases</p>
        <p class='metric-value'>{total_cases:,}</p>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[1]:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-icon'>{ICON_CALENDAR_START}</div>
        <p class='metric-label'>First Reported Year</p>
        <p class='metric-value'>{first_reported_year}</p>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[2]:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-icon'>{ICON_CALENDAR_END}</div>
        <p class='metric-label'>Last Reported Year</p>
        <p class='metric-value'>{last_reported_year}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # Close margin-bottom wrapper




# ─── Charts Section ─────────────────────────────────────────────────────────
# Arrange charts in columns: bar chart (wider) and map chart
charts_col1, charts_col2 = st.columns([0.65, 0.35], gap="large")

with charts_col1:
    # Bar Chart: Filtered Data Breakdown
    st.markdown("<div class='chart-title'>Filtered Data Breakdown</div>", unsafe_allow_html=True)
    # Aggregate data for the bar chart
    bar_data = df_filtered.groupby('Year')['Cases'].sum().reset_index()
    fig_bar = px.bar(
        bar_data,
        x='Year',
        y='Cases',
        labels={'Cases': 'Number of Cases', 'Year': 'Year'},
        template='plotly_white' # Use a clean Plotly template
    )
    fig_bar.update_layout(
        margin=dict(t=30, l=60, r=20, b=40), # Adjust chart margins
        yaxis_title="Number of Cases",
        xaxis_title="Year"
    )
    st.plotly_chart(fig_bar, use_container_width=True) # Display chart, fit to column width

with charts_col2:
    # Map Chart: Cases by County
    st.markdown("<div class='chart-title'>Cases by County Map</div>", unsafe_allow_html=True)
    # Aggregate data for the map
    map_data = df_filtered.groupby('County')['Cases'].sum().reset_index()
    map_data['County'] = map_data['County'].str.title() # Ensure county names are title case for matching

    fig_map = px.choropleth_mapbox(
        map_data,
        geojson=counties_geo,
        locations='County', # Column in map_data for locations
        featureidkey=geojson_feature_key, # Path to feature id in GeoJSON
        color='Cases', # Column for color scale
        color_continuous_scale="Viridis", # Color scale for the choropleth
        range_color=(0, map_data['Cases'].max() if not map_data.empty else 1), # Dynamic color range
        mapbox_style='carto-positron', # Mapbox style
        center={'lat': 37.5, 'lon': -119.5}, # Center of the map
        zoom=4.5, # Initial zoom level
        opacity=0.7, # Opacity of the choropleth layer
        hover_data={'County': True, 'Cases': True} # Data to show on hover
    )
    fig_map.update_layout(
        margin=dict(t=30, l=0, r=0, b=0), # Adjust map margins
        coloraxis_colorbar=dict(title="Cases") # Title for the color bar
    )
    st.plotly_chart(fig_map, use_container_width=True)

# Cases Over Time (Area Chart) - Full Width
st.markdown("<div class='chart-title' style='margin-top: 2rem;'>Cases Over Time</div>", unsafe_allow_html=True)
# Data for area chart is typically aggregated year/cases, same as bar_data
line_data = bar_data.copy()
fig_line = px.area(
    line_data,
    x='Year',
    y='Cases',
    labels={'Cases': 'Number of Cases', 'Year': 'Year'},
    template='plotly_white'
)
fig_line.update_layout(
    margin=dict(t=30, l=60, r=20, b=40),
    yaxis_title="Number of Cases",
    xaxis_title="Year"
)
# Customize the fill and line color of the area chart
fig_line.update_traces(fillcolor='rgba(74,144,226,0.3)', line=dict(color='rgba(74,144,226,1)'))
st.plotly_chart(fig_line, use_container_width=True)

# Reminder about data file location if they were initially not found
if not os.path.exists(os.path.join(os.path.dirname(__file__), 'california_infectious_diseases.csv')):
    st.caption("Reminder: `california_infectious_diseases.csv` and `california-counties.geojson` must be in the same directory as this script for the dashboard to function correctly.")
