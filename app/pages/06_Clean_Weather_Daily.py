# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
import time

from pipeline.weather import transform
from components.table_explorer import render_table_explorer


# ----------------------------------
# Page Config
# ----------------------------------
st.set_page_config(layout="wide")

st.title("🌦 Transform Weather Data")
st.caption("Bronze → Silver cleaning pipeline for daily weather data")

st.divider()


# ==================================
# Control Panel
# ==================================
st.subheader("⚙️ Transform Controls")

col1, col2 = st.columns([2, 1])

with col1:
    truncate = st.checkbox(
        "Truncate silver.weather_daily before transform",
        value=False,
        help="Clears silver layer before inserting transformed records."
    )

with col2:
    run_clicked = st.button(
        "🚀 Run Weather Transform",
        type="primary",
        use_container_width=True
    )


# ----------------------------------
# Execution Section
# ----------------------------------
if run_clicked:

    start_time = time.perf_counter()
    status_placeholder = st.empty()

    try:
        with st.spinner("Transforming bronze → silver weather data..."):
            result = transform(truncate=truncate)

        elapsed = time.perf_counter() - start_time

        status_placeholder.success("✅ Weather transform completed")

        m1, m2 = st.columns(2)
        m1.metric("Rows Written", f"{result['rows_written']:,}")
        m2.metric("Execution Time (sec)", f"{elapsed:.2f}")

    except Exception:
        import traceback
        status_placeholder.error("❌ Transform failed")
        st.code(traceback.format_exc())

st.divider()


# ==================================
# Data Layers
# ==================================
layer_col1, layer_col2 = st.columns(2)

with layer_col1:
    st.markdown("### 🥉 Bronze Layer")
    render_table_explorer(
        table_name="bronze.weather_daily",
        session_key="bronze_weather_daily_transform",
        metric_label="Bronze Weather Rows",
        allow_truncate=True,
    )

with layer_col2:
    st.markdown("### 🥈 Silver Layer")
    render_table_explorer(
        table_name="silver.weather_daily",
        session_key="silver_weather_daily",
        metric_label="Silver Weather Rows",
        allow_truncate=True,
    )
