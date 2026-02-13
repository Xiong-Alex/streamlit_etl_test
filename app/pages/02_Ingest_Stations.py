# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
from pathlib import Path

from pipeline.stations import ingest
from components.directory_viewer import render_directory_view
from components.table_explorer import render_table_explorer
from components.db import get_engine


# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/stations")


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Stations: Ingest to Bronze")


# ----------------------------------
# Landing Directory
# ----------------------------------
render_directory_view(
    directory=LANDING_DIR,
    title="Landing Directory",
    session_key="stations_landing"
)

st.divider()


# ----------------------------------
# Ingest Button
# ----------------------------------
engine = get_engine()

if st.button("Ingest Stations into Bronze", width="stretch"):
    try:
        result = ingest(engine)
        st.success(
            f"Inserted {result['rows_inserted']:,} rows into "
            f"{result['table']}"
        )
    except Exception as e:
        st.error(f"Ingest failed: {e}")

st.divider()


# ----------------------------------
# Bronze Table Explorer
# ----------------------------------
render_table_explorer(
    table_name="bronze.stations",
    session_key="bronze_stations",
    metric_label="Bronze Station Rows",
    allow_truncate=True,
    truncate_sql="TRUNCATE TABLE bronze.stations;",
    default_limit=20,
)
