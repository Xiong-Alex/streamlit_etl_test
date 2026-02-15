# ----------------------------------
# Imports
# ----------------------------------
import time
import threading
from datetime import date
from pathlib import Path
import streamlit as st
import pandas as pd
from sqlalchemy import text

from components.db import get_engine
from components.directory_viewer import render_directory_view
from pipeline.weather import download


# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/weather")
LANDING_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------
# Page Header
# ----------------------------------
st.title("Weather: NOAA Daily Downloader")
st.caption("Download GHCN daily weather files into landing layer")

st.divider()

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
# Scope Controls
# ----------------------------------
st.subheader("🌎 Station Scope")

mode = st.radio(
    "Station Scope",
    ["Select States", "All US"],
    index=0,  # default to Select States
    horizontal=True
)

if mode == "Select States":
    selected_states = st.multiselect(
        "Choose states",
        all_states,
        default=["GA"] if "GA" in all_states else []
    )
else:
    selected_states = all_states

# ----------------------------------
# Station Count
# ----------------------------------
if selected_states:
    placeholders = ",".join([f":s{i}" for i in range(len(selected_states))])
    query = text(f"""
        SELECT COUNT(*)
        FROM silver.stations
        WHERE state IN ({placeholders})
    """)
    params = {f"s{i}": s for i, s in enumerate(selected_states)}

    station_count = pd.read_sql(query, engine, params=params).iloc[0, 0]
    st.info(f"📍 Stations Selected: {station_count:,}")
else:
    station_count = 0
    st.warning("No states selected.")


st.divider()


# ----------------------------------
# Date + Performance Controls
# ----------------------------------
st.subheader("⚙️ Download Settings")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date", date(2016, 1, 1))

with col2:
    end_date = st.date_input("End Date", date(2023, 12, 31))


max_workers = st.slider(
    "Download Threads",
    min_value=4,
    max_value=20,
    value=12
)


# ----------------------------------
# Execute Download
# ----------------------------------
if st.button("Download Weather Data", type="primary", use_container_width=True):

    if not selected_states:
        st.warning("No states selected.")
        st.stop()

    start_time = time.perf_counter()

    progress_bar = st.progress(0)
    status_text = st.empty()

    starting_files = len(list(LANDING_DIR.glob("*.csv")))
    result_container = {}

    def run_download():
        result_container["result"] = download(
            states=selected_states,
            start_date=start_date,
            end_date=end_date,
            max_workers=max_workers
        )

    thread = threading.Thread(target=run_download)
    thread.start()

    while thread.is_alive():
        current_files = len(list(LANDING_DIR.glob("*.csv"))) - starting_files
        current_files = max(current_files, 0)

        percent = (
            min(int((current_files / station_count) * 100), 100)
            if station_count > 0 else 0
        )

        progress_bar.progress(percent)
        status_text.text(
            f"{current_files:,} / {station_count:,} files downloaded"
        )

        time.sleep(0.5)

    thread.join()

    elapsed = time.perf_counter() - start_time

    progress_bar.progress(100)
    status_text.text("Download complete")

    st.success("Weather download completed")

    st.write(f"📦 Files downloaded: {result_container.get('result', {}).get('downloaded', 'N/A')}")
    st.write(f"⏱ Time: {elapsed:.2f} sec")

    if elapsed > 0:
        st.write(f"⚡ Files/sec: {current_files / elapsed:,.2f}")

    st.rerun()


st.divider()


# ----------------------------------
# Landing Directory
# ----------------------------------
st.subheader("📂 Landing Directory")

render_directory_view(
    LANDING_DIR,
    title=None,
    session_key="weather_landing"
)
