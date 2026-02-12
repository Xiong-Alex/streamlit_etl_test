# ----------------------------------
# Imports
# ----------------------------------
import time
import csv
import requests
from pathlib import Path
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
from sqlalchemy import text

from components.db import get_engine
from components.directory_viewer import render_directory_view


# ----------------------------------
# Page Title
# ----------------------------------
st.title("US Weather Downloader")


# ----------------------------------
# Config
# ----------------------------------
BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"
OUT_DIR = Path("/data/landing/weather")
ARCHIVE_DIR = Path("/data/archive/weather")

OUT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

engine = get_engine()


# ----------------------------------
# Fetch Available States (US Only)
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
    st.warning("No stations found in database. Please ingest and transform stations first.")
    st.stop()

all_states = states_df["state"].tolist()


# ----------------------------------
# UI Controls
# ----------------------------------
mode = st.radio("Station Scope", ["All US", "Select States"])

if mode == "Select States":
    selected_states = st.multiselect("Choose states", all_states)
else:
    selected_states = all_states

start_date = st.date_input("Start Date", date(2015, 1, 1))
end_date = st.date_input("End Date", date.today())

MAX_WORKERS = st.slider("Max Threads", 4, 20, 12)


# ----------------------------------
# Fetch Station IDs
# ----------------------------------
if selected_states:

    placeholders = ",".join([f":state{i}" for i in range(len(selected_states))])

    query = text(f"""
        SELECT station_id
        FROM silver.stations
        WHERE state IN ({placeholders})
    """)

    params = {f"state{i}": s for i, s in enumerate(selected_states)}

    station_ids = pd.read_sql(query, engine, params=params)["station_id"].tolist()

else:
    station_ids = []

st.metric("Stations Selected", len(station_ids))


# ----------------------------------
# Download Function
# ----------------------------------
def download_weather_to_csv(station_id: str):

    out_csv = OUT_DIR / f"{station_id}.csv"
    url = f"{BASE_URL}/{station_id}.dly"

    if out_csv.exists():
        return

    r = requests.get(url, timeout=60)
    r.raise_for_status()

    with open(out_csv, "w", newline="") as fout:
        writer = csv.writer(fout)

        writer.writerow([
            "station_id",
            "obs_date",
            "element",
            "value",
            "m_flag",
            "q_flag",
            "s_flag",
        ])

        for line in r.text.splitlines():
            station = line[0:11].strip()
            year = int(line[11:15])
            month = int(line[15:17])
            element = line[17:21]

            for day in range(1, 32):
                base = 21 + (day - 1) * 8
                value = line[base:base+5].strip()
                m_flag = line[base+5].strip()
                q_flag = line[base+6].strip()
                s_flag = line[base+7].strip()

                if value == "-9999":
                    continue

                try:
                    obs_date = date(year, month, day)
                except ValueError:
                    continue

                if not (start_date <= obs_date <= end_date):
                    continue

                writer.writerow([
                    station,
                    obs_date.isoformat(),
                    element,
                    int(value),
                    m_flag or None,
                    q_flag or None,
                    s_flag or None,
                ])


# ----------------------------------
# Execute Download
# ----------------------------------
if st.button("Download Weather Data", use_container_width=True):

    if not station_ids:
        st.warning("No stations selected.")
        st.stop()

    progress = st.progress(0)
    status = st.empty()

    start_time = time.perf_counter()

    completed = 0
    failed = 0
    total = len(station_ids)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        future_to_sid = {
            executor.submit(download_weather_to_csv, sid): sid
            for sid in station_ids
        }

        for i, future in enumerate(as_completed(future_to_sid)):

            sid = future_to_sid[future]

            try:
                future.result()
                completed += 1
            except Exception as e:
                failed += 1
                st.error(f"Failed: {sid} → {e}")

            progress.progress((i + 1) / total)
            status.write(f"Completed: {completed} | Failed: {failed}")

    elapsed = time.perf_counter() - start_time

    st.success("Download complete")
    st.write(f"Time: {elapsed:.2f} sec")
    st.write(f"Stations/sec: {completed / elapsed:.2f}")

    st.rerun()


# ==================================
# Landing & Archive Directory Views
# ==================================
st.divider()

render_directory_view("Landing Directory", OUT_DIR)

st.divider()

render_directory_view("Archive Directory", ARCHIVE_DIR)


# Optional clear landing button
if st.button("🗑 Clear Landing Directory", use_container_width=True):
    for f in OUT_DIR.glob("*.csv"):
        f.unlink()
    st.success("Landing directory cleared.")
    st.rerun()
