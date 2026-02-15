# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
import time

from pipeline.weather_daily_pivot import build
from components.table_explorer import render_table_explorer


# ----------------------------------
# Page Config
# ----------------------------------
st.set_page_config(layout="wide")

st.title("🌤 Weather: Daily Pivot (Silver)")
st.caption("Build / refresh silver.weather_daily_pivot materialized view")

st.divider()


# ----------------------------------
# Controls Section
# ----------------------------------
st.subheader("⚙️ Build Controls")

col1, col2 = st.columns([2, 1])

with col1:
    concurrent = st.checkbox(
        "Use CONCURRENT refresh (requires unique index)",
        value=False,
        help="Allows reads during refresh but requires unique index on the materialized view."
    )

with col2:
    run_clicked = st.button(
        "🚀 Build Weather Daily Pivot",
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
        with st.spinner("Refreshing weather_daily_pivot..."):
            result = build(concurrent=concurrent)

        elapsed = time.perf_counter() - start_time

        rows = result["rows_refreshed"]
        seconds = result["seconds"]

        status_placeholder.success("✅ Pivot refreshed successfully")

        m1, m2, m3 = st.columns(3)
        m1.metric("Rows in Pivot", f"{rows:,}")
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
st.markdown("### 🥈 Silver Layer: weather_daily_pivot")

render_table_explorer(
    table_name="silver.weather_daily_pivot",
    session_key="silver_weather_daily_pivot",
    metric_label="Weather Daily Pivot Rows",
    # can not truncate matterialize view, utilize refresh
)