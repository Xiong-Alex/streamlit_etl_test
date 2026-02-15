# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
import time

from pipeline.accident_weather import build
from components.table_explorer import render_table_explorer


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Gold: Build Accident + Weather")
st.caption("Create analytics-ready gold.accident_weather fact table")

st.divider()


# ----------------------------------
# Controls Section
# ----------------------------------
st.subheader("⚙️ Build Options")

truncate = st.checkbox(
    "Truncate gold.accident_weather before rebuild",
    value=False,
    help="Clears gold table before rebuilding."
)

if st.button("🚀 Build Gold Accident Weather", type="primary", use_container_width=True):

    try:
        with st.spinner("Building gold.accident_weather..."):
            result = build(truncate=truncate)

        rows = result["rows_written"]
        seconds = result["seconds"]

        st.success("Gold table built successfully")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rows Written", f"{rows:,}")
        col2.metric("Time (sec)", f"{seconds:.2f}")

        if seconds > 0:
            col3.metric("Rows / Sec", f"{rows / seconds:,.0f}")

    except Exception:
        import traceback
        st.error("Build failed")
        st.code(traceback.format_exc())


st.divider()


# ----------------------------------
# Gold Table Explorer
# ----------------------------------
st.subheader("📊 Gold Layer Preview")

render_table_explorer(
    table_name="gold.accident_weather",
    session_key="gold_accident_weather",
    metric_label="Gold Accident Weather Rows",
    allow_truncate=True,
)
