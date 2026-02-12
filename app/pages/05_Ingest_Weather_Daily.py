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
st.title("Weather Bronze Ingest (Threaded COPY)")


# ----------------------------------
# Paths
# ----------------------------------
LANDING_DIR = Path("/data/landing/weather")
ARCHIVE_DIR = Path("/data/archive/weather")


# ----------------------------------
# 1️⃣ Ingest Panel
# ----------------------------------
render_ingest_panel(
    dataset_name="Weather",
    landing_dir=LANDING_DIR,
    archive_dir=ARCHIVE_DIR,
    table_name="bronze.weather_daily",
    copy_sql="""
        COPY bronze.weather_daily (
            station_id,
            obs_date,
            element,
            value,
            m_flag,
            q_flag,
            s_flag
        )
        FROM STDIN
        WITH CSV HEADER
    """,
    session_key="weather_ingest",
    max_threads=8,
    default_threads=4,
)


# ----------------------------------
# 2️⃣ Table Explorer
# ----------------------------------
st.divider()

render_table_explorer(
    table_name="bronze.weather_daily",
    session_key="bronze_weather",
    metric_label="Bronze Weather Rows",
    allow_truncate=True,
    truncate_sql="TRUNCATE TABLE bronze.weather_daily;",
)
