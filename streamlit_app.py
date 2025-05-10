# streamlit_app.py
import threading
import dash_app    # assumes your Dash code is in dashboard.py and you’ve renamed the file to dash_app.py
from dash_app import app  # import your Dash app object
import streamlit as st
from streamlit.components.v1 import html

def run_dash() -> None:
    # Dash’s built-in server
    app.run_server(host="0.0.0.0", port=8050)

# Start Dash in background
thread = threading.Thread(target=run_dash, daemon=True)
thread.start()

# Streamlit page
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")
st.title("California Infectious Disease Dashboard")
st.markdown("_Data from 2001–2023 (Provisional)_")

# Embed the running Dash app
html(
    '<iframe src="http://localhost:8050" '
    'width="100%" height="800" style="border:none;"></iframe>',
    height=810
)
