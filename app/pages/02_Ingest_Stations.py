# ----------------------------------
# Imports
# ----------------------------------
from pathlib import Path
import streamlit as st

from components.ingest_panel import render_ingest_panel
from components.table_explorer import render_table_explorer


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Station Bronze Ingest")


# ----------------------------------
# Paths
# ----------------------------------
LANDING_DIR = Path("/data/landing/stations")
ARCHIVE_DIR = Path("/data/archive/stations")


# ----------------------------------
# 1️⃣ Ingest Panel
# ----------------------------------
render_ingest_panel(
    dataset_name="Stations",
    landing_dir=LANDING_DIR,
    archive_dir=ARCHIVE_DIR,
    table_name="bronze.stations",
    copy_sql="""
        COPY bronze.stations (
            station_id,
            latitude,
            longitude,
            elevation,
            state,
            name,
            gsn,
            hcn,
            wmo
        )
        FROM STDIN
        WITH CSV HEADER
    """,
    session_key="stations_ingest",
)


# ----------------------------------
# 2️⃣ Table Explorer
# ----------------------------------
st.divider()

render_table_explorer(
    table_name="bronze.stations",
    session_key="bronze_stations",
    metric_label="Bronze Station Rows",
    allow_truncate=True,
    truncate_sql="TRUNCATE TABLE bronze.stations;",
)
