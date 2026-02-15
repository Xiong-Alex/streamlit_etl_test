# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
from pathlib import Path
import time

from pipeline.accidents import ingest
from components.directory_viewer import render_directory_view
from components.table_explorer import render_table_explorer
from components.logger import get_logger


logger = get_logger(__name__)


# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/accidents")


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Accidents: Ingest to Bronze")
st.caption("Load accident CSV files into bronze.us_accidents")

st.divider()


# ----------------------------------
# Landing Directory
# ----------------------------------
render_directory_view(
    directory=LANDING_DIR,
    title="Landing Directory",
    session_key="accidents_landing"
)

st.divider()


# ----------------------------------
# Ingest Controls
# ----------------------------------
st.markdown("## Ingest Controls")

truncate = st.checkbox(
    "Truncate bronze.us_accidents before ingest",
    value=False,
    help="Clear bronze table before loading."
)

if st.button(
    "Ingest Accidents into Bronze",
    type="primary",
    use_container_width=True
):

    start_time = time.perf_counter()

    try:
        with st.spinner("Ingesting accident files..."):
            result = ingest(truncate=truncate)

        rows = result["rows_inserted"]
        seconds = result["seconds"]

        st.success("Ingest completed successfully")

        st.write(f"📦 Rows inserted: {rows:,}")
        st.write(f"⏱ Time: {seconds:.2f} seconds")

        if seconds > 0:
            st.write(f"⚡ Rows/sec: {rows / seconds:,.0f}")

        # Force UI refresh after successful ingest
        st.rerun()

    except Exception as e:
        logger.exception("Accident ingest failed")
        st.error(f"Ingest failed: {e}")


st.divider()


# ----------------------------------
# Bronze Table Explorer
# ----------------------------------
st.markdown("## Bronze Layer")

render_table_explorer(
    table_name="bronze.us_accidents",
    session_key="bronze_us_accidents",
    metric_label="Bronze Accident Rows",
    allow_truncate=True,
)
