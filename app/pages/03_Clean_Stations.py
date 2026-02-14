import time
import streamlit as st
from pipeline.stations import transform
from components.table_explorer import render_table_explorer
from components.db import get_engine



engine = get_engine()

st.title("Transform Stations: Bronze → Silver")

truncate_silver = st.checkbox(
    "Truncate silver.stations before transform",
    value=False
)

if st.button("Run Bronze → Silver Transform", width="stretch"):

    start = time.perf_counter()

    try:
        transform(engine, truncate=truncate_silver)

        elapsed = time.perf_counter() - start

        st.success("Transform complete")
        st.write(f"Time: {elapsed:.2f} seconds")

    except Exception as e:
        import traceback
        st.error("Transform failed")
        st.code(traceback.format_exc())

st.markdown("## Bronze Layer")
render_table_explorer(
    table_name="bronze.stations",
    session_key="bronze_stations_transform",
    metric_label="Bronze Rows",
    allow_truncate=True,
    truncate_sql="TRUNCATE TABLE bronze.stations;",
)

st.markdown("## Silver Layer")
render_table_explorer(
    table_name="silver.stations",
    session_key="silver_stations",
    metric_label="Silver Rows",
    allow_truncate=True,
    truncate_sql="TRUNCATE TABLE silver.stations;",
)
