# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
import time

from pipeline.accident_station_map import build
from components.table_explorer import render_table_explorer
from components.logger import get_logger


logger = get_logger(__name__)


# ----------------------------------
# Page Config
# ----------------------------------
st.set_page_config(layout="wide")

st.title("🗺 Accident → Station Mapping")
st.caption("Map each accident to its nearest weather station (Silver Layer)")

st.divider()


# ----------------------------------
# Controls Section
# ----------------------------------
st.subheader("⚙️ Build Controls")

col1, col2 = st.columns([2, 1])

with col1:
    truncate = st.checkbox(
        "Truncate silver.accident_station_map before build",
        value=False,
        help="Clears existing mappings before rebuilding."
    )

with col2:
    run_clicked = st.button(
        "🚀 Build Accident → Station Map",
        type="primary",
        use_container_width=True
    )


# ----------------------------------
# Execution
# ----------------------------------
if run_clicked:

    start_time = time.perf_counter()
    status_placeholder = st.empty()

    try:
        with st.spinner("Computing nearest stations using KNN search..."):
            result = build(truncate=truncate)

        elapsed = time.perf_counter() - start_time

        rows = result["rows_mapped"]
        seconds = result["seconds"]

        status_placeholder.success("✅ Mapping completed successfully")

        m1, m2, m3 = st.columns(3)
        m1.metric("Rows Mapped", f"{rows:,}")
        m2.metric("Execution Time (sec)", f"{seconds:.2f}")
        m3.metric(
            "Rows / Sec",
            f"{rows / seconds:,.0f}" if seconds > 0 else "—"
        )

    except Exception:
        import traceback
        status_placeholder.error("❌ Build failed")
        st.code(traceback.format_exc())


st.divider()


# ----------------------------------
# Data Explorer
# ----------------------------------
st.markdown("### 🥈 Silver Layer: accident_station_map")

render_table_explorer(
    table_name="silver.accident_station_map",
    session_key="silver_accident_station_map",
    metric_label="Accident → Station Mappings",
    allow_truncate=True,
)
