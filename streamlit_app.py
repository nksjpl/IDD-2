# streamlit_app.py
import threading
from dash_app import app
import streamlit as st
from streamlit.components.v1 import html

def run_dash():
    app.run_server(host="0.0.0.0", port=8050)

# Start Dash in background thread
thread = threading.Thread(target=run_dash, daemon=True)
thread.start()

# Streamlit layout
st.set_page_config(page_title="California Infectious Disease Dashboard", layout="wide")
st.title("California Infectious Disease Dashboard")
st.markdown("_Data from 2001–2023 (Provisional)_")

# Embed Dash app via iframe
html(
    '<iframe src="http://localhost:8050" '
    'width="100%" height="800" style="border:none;"></iframe>',
    height=810
)
