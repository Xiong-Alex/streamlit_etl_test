# ==================================
# Imports
# ==================================
import streamlit as st


# ==================================
# Page Config
# ==================================
st.set_page_config(
    page_title="Weather ETL Pipeline",
    page_icon="🌦",
    layout="wide"
)


# ==================================
# Hero Header
# ==================================
st.markdown("""
# 🌦 Weather + Accidents ETL Platform  
### Bronze → Silver → Gold Data Pipeline

A modular, production-style ETL workflow combining  
NOAA weather data and US accident records into analytics-ready datasets.
""")

st.divider()


# ==================================
# Pipeline Overview Cards
# ==================================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🥉 Bronze")
    st.caption("Raw ingested data")
    st.info(
        """
        - Stations  
        - Weather Daily  
        - US Accidents  
        """
    )

with col2:
    st.markdown("### 🥈 Silver")
    st.caption("Cleaned + transformed data")
    st.info(
        """
        - Clean Stations  
        - Clean Weather  
        - Clean Accidents  
        - Accident → Station Map  
        """
    )

with col3:
    st.markdown("### 🥇 Gold")
    st.caption("Analytics-ready fact tables")
    st.info(
        """
        - accident_weather  
        """
    )


st.divider()


# ==================================
# Run Section
# ==================================
st.markdown("## 🚀 Run Pipeline")

col1, col2 = st.columns([2, 1])

with col1:
    st.button(
        "Run Full Pipeline",
        type="primary",
        use_container_width=True
    )

with col2:
    st.metric("Status", "Idle")

st.caption("Runs the entire Bronze → Silver → Gold pipeline in one execution.")


st.divider()


# ==================================
# Logs Section
# ==================================
st.markdown("## 📜 Execution Logs")

st.code(
"""[INFO] Pipeline ready.
[INFO] Awaiting execution.
[INFO] No active jobs.""",
language="bash"
)


st.divider()


# ==================================
# Analytics Section
# ==================================
st.markdown("## 📈 Analytics Preview")

st.info(
    """
    Analytics dashboards and KPIs will appear here  
    after successful pipeline execution.
    """
)
