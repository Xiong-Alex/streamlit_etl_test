# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
from pathlib import Path
import time

from pipeline.stations import ingest
from components.directory_viewer import render_directory_view
from components.table_explorer import render_table_explorer


# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/stations")
LANDING_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------
# Page Header
# ----------------------------------
st.title("Stations: Ingest to Bronze")
st.caption("Load landing station CSV into bronze.stations")

st.divider()


# ----------------------------------
# Landing Directory
# ----------------------------------
st.subheader("📂 Landing Directory")

render_directory_view(
    directory=LANDING_DIR,
    title=None,
    session_key="stations_landing"
)

st.divider()


# ----------------------------------
# Ingest Controls
# ----------------------------------
st.subheader("⚙️ Ingest Controls")

truncate = st.checkbox(
    "Truncate bronze.stations before ingest",
    value=False,
    help="Clears bronze.stations before loading new data."
)

if st.button("Ingest Stations into Bronze", type="primary", use_container_width=True):

    try:
        start_time = time.perf_counter()

        with st.spinner("Ingesting stations into bronze..."):
            result = ingest(truncate=truncate)

        elapsed = time.perf_counter() - start_time

        st.success("Stations ingest completed successfully")

        st.write(f"📦 Rows inserted: {result['rows_inserted']:,}")
        st.write(f"⏱ Time: {elapsed:.2f} sec")

        if elapsed > 0:
            st.write(f"⚡ Rows/sec: {result['rows_inserted'] / elapsed:,.0f}")

        st.rerun()

    except Exception:
        import traceback
        st.error("Ingest failed")
        st.code(traceback.format_exc())


st.divider()


# ----------------------------------
# Bronze Table Explorer
# ----------------------------------
st.subheader("🗄 Bronze Layer")

render_table_explorer(
    table_name="bronze.stations",
    session_key="bronze_stations",
    metric_label="Bronze Station Rows",
    allow_truncate=True,
)