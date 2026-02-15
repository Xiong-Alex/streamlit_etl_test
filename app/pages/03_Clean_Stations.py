# ----------------------------------
# Imports
# ----------------------------------
import time
import streamlit as st

from pipeline.stations import transform
from components.table_explorer import render_table_explorer


# ----------------------------------
# Page Config
# ----------------------------------
st.set_page_config(layout="wide")

st.title("🧼 Transform Stations")
st.caption("Bronze → Silver data cleaning pipeline")

st.divider()


# ==================================
# Control Panel
# ==================================
st.subheader("⚙️ Transform Controls")

col1, col2 = st.columns([2, 1])

with col1:
    truncate_silver = st.checkbox(
        "Truncate silver.stations before transform",
        value=False,
        help="Clears silver layer before inserting new records."
    )

with col2:
    run_clicked = st.button(
        "🚀 Run Station Transform",
        use_container_width=True,
        type="primary"
    )

# ----------------------------------
# Execution
# ----------------------------------
if run_clicked:

    start = time.perf_counter()

    status_placeholder = st.empty()

    try:
        with st.spinner("Transforming bronze → silver..."):
            result = transform(truncate=truncate_silver)

        elapsed = time.perf_counter() - start

        status_placeholder.success("✅ Transform complete")

        # Metrics Row
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
        table_name="bronze.stations",
        session_key="bronze_stations_transform",
        metric_label="Bronze Rows",
        allow_truncate=True,
    )

with layer_col2:
    st.markdown("### 🥈 Silver Layer")
    render_table_explorer(
        table_name="silver.stations",
        session_key="silver_stations",
        metric_label="Silver Rows",
        allow_truncate=True,
    )
