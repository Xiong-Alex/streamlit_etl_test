# ==================================
# Imports
# ==================================
import streamlit as st
import time

from pipeline.accidents import transform
from components.table_explorer import render_table_explorer


# ==================================
# Page Config
# ==================================
st.set_page_config(layout="wide")

st.title("🚗 Transform Accidents Data")
st.caption("Bronze → Silver cleaning pipeline for US accidents dataset")

st.divider()


# ==================================
# Scope Selection
# ==================================
st.subheader("🌎 Scope")

mode = st.radio(
    "Transform Scope",
    ["Select States", "All States"],
    index=0,
    horizontal=True
)

if mode == "Select States":
    selected_states = st.multiselect(
        "Choose States",
        options=["GA"],   # Replace with dynamic list later if desired
        default=["GA"]
    )
else:
    selected_states = None

st.divider()


# ==================================
# Transform Settings
# ==================================
st.subheader("⚙️ Transform Settings")

col1, col2 = st.columns([2, 1])

with col1:
    truncate_silver = st.checkbox(
        "Truncate silver.us_accidents before transform",
        value=False,
        help="Clears silver layer before inserting transformed records."
    )

with col2:
    run_clicked = st.button(
        "🚀 Run Accidents Transform",
        type="primary",
        use_container_width=True
    )

# ----------------------------------
# Weather Date Restriction Checkbox
# ----------------------------------
restrict_weather = st.checkbox(
    "Restrict to Silver Weather Date Range",
    value=True,
    help="Only process accidents within min/max dates of silver.weather_daily"
)


# ==================================
# Execution
# ==================================
if run_clicked:

    start_time = time.perf_counter()
    status_placeholder = st.empty()

    try:
        with st.spinner("Transforming bronze → silver accidents data..."):
            result = transform(
                truncate=truncate_silver,
                states=selected_states,
                restrict_to_weather_range=restrict_weather
            )

        elapsed = time.perf_counter() - start_time

        rows = result["rows_written"]
        seconds = result["seconds"]

        status_placeholder.success("✅ Transform completed")

        m1, m2, m3 = st.columns(3)
        m1.metric("Rows Written", f"{rows:,}")
        m2.metric("Execution Time (sec)", f"{seconds:.2f}")
        m3.metric(
            "Rows / Sec",
            f"{rows / seconds:,.0f}" if seconds > 0 else "—"
        )

    except Exception:
        import traceback
        status_placeholder.error("❌ Transform failed")
        st.code(traceback.format_exc())


st.divider()


# ==================================
# Data Layers
# ==================================
layer1, layer2 = st.columns(2)

with layer1:
    st.markdown("### 🥉 Bronze Layer")
    render_table_explorer(
        table_name="bronze.us_accidents",
        session_key="bronze_us_accidents_transform",
        metric_label="Bronze Accident Rows",
        allow_truncate=True,
    )

with layer2:
    st.markdown("### 🥈 Silver Layer")
    render_table_explorer(
        table_name="silver.us_accidents",
        session_key="silver_us_accidents",
        metric_label="Silver Accident Rows",
        allow_truncate=True,
    )
