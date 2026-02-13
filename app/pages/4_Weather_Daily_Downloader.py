# ----------------------------------
# Imports
# ----------------------------------
import time
from datetime import date
from pathlib import Path
import streamlit as st
import pandas as pd
from sqlalchemy import text

from components.db import get_engine
from components.directory_viewer import render_directory_view
from pipeline.weather import download


# ----------------------------------
# Page Title
# ----------------------------------
st.title("NOAA Weather Daily Downloader")


engine = get_engine()


# ----------------------------------
# Fetch Available States
# ----------------------------------
states_df = pd.read_sql(
    text("""
        SELECT DISTINCT state
        FROM silver.stations
        WHERE state IS NOT NULL
        ORDER BY state
    """),
    engine
)

if states_df.empty:
    st.warning("No stations found. Please ingest and transform stations first.")
    st.stop()

all_states = states_df["state"].tolist()


# ----------------------------------
# UI Controls
# ----------------------------------
mode = st.radio(
    "Station Scope",
    ["All US (Default)", "Select States"]
)

if mode == "Select States":
    selected_states = st.multiselect("Choose states", all_states)
else:
    selected_states = all_states

start_date = st.date_input("Start Date", date(2015, 1, 1))
end_date = st.date_input("End Date", date.today())

max_workers = st.slider("Download Threads", 4, 20, 12)


# ----------------------------------
# Execute Download
# ----------------------------------
if st.button("Download Weather Data", width="stretch"):

    if not selected_states:
        st.warning("No states selected.")
        st.stop()

    start_time = time.perf_counter()

    try:
        result = download(
            engine,
            states=selected_states,
            start_date=start_date,
            end_date=end_date,
            max_workers=max_workers
        )

        elapsed = time.perf_counter() - start_time

        st.success("Download complete")
        st.write(result)
        st.write(f"Time: {elapsed:.2f} sec")

    except Exception:
        import traceback
        st.error("Download failed")
        st.code(traceback.format_exc())

# ----------------------------------
# Landing Directory Viewer
# ----------------------------------
LANDING_DIR = Path("/data/landing/weather")

render_directory_view(
    LANDING_DIR,
    title="Landing Directory",
    session_key="weather_landing"
)