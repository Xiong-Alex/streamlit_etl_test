# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
from pathlib import Path
import threading
import time

from pipeline.weather import ingest
from components.directory_viewer import render_directory_view
from components.table_explorer import render_table_explorer


# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/weather")


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Weather: Ingest to Bronze")
st.caption("Load weather CSV files into bronze.weather_daily")

st.divider()


# ----------------------------------
# Landing Directory Viewer
# ----------------------------------
render_directory_view(
    directory=LANDING_DIR,
    title="Landing Directory",
    session_key="weather_landing"
)

st.divider()


# ----------------------------------
# Ingest Controls
# ----------------------------------
st.subheader("⚙️ Ingest Settings")

max_workers = st.slider(
    "Ingest Threads",
    min_value=1,
    max_value=12,
    value=4,
    help="Number of threads to speed up ingestion"
)

if st.button("Ingest Weather into Bronze", type="primary", use_container_width=True):

    files_before = list(LANDING_DIR.glob("*.csv"))
    total_files = len(files_before)

    if total_files == 0:
        st.warning("No files in landing directory.")
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()

    result_container = {}

    def run_ingest():
        result_container["result"] = ingest(max_workers=max_workers)

    start_time = time.perf_counter()

    thread = threading.Thread(target=run_ingest)
    thread.start()

    while thread.is_alive():
        remaining_files = len(list(LANDING_DIR.glob("*.csv")))
        completed = total_files - remaining_files

        percent = int((completed / total_files) * 100)
        progress_bar.progress(min(percent, 100))
        status_text.text(f"{completed:,} / {total_files:,} files ingested")

        time.sleep(0.5)

    thread.join()

    elapsed = time.perf_counter() - start_time

    progress_bar.progress(100)
    status_text.text("Ingest complete")

    result = result_container.get("result", {})
    rows = result.get("rows_inserted", 0)

    st.success("Weather ingest completed successfully")

    st.write(f"📦 Rows inserted: {rows:,}")
    st.write(f"⏱ Time: {elapsed:.2f} sec")

    if elapsed > 0:
        st.write(f"⚡ Rows/sec: {rows / elapsed:,.0f}")

    st.rerun()


st.divider()


# ----------------------------------
# Bronze Table Explorer
# ----------------------------------
render_table_explorer(
    table_name="bronze.weather_daily",
    session_key="bronze_weather_daily",
    metric_label="Bronze Weather Rows",
    allow_truncate=True,
)
