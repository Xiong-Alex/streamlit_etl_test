# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
from pathlib import Path
import pandas as pd

from pipeline.accidents import download
from components.directory_viewer import render_directory_view


# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/accidents")
LANDING_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Accidents: Download to Landing")
st.caption("Download and stage US Accidents dataset (Kaggle)")

st.divider()


# ----------------------------------
# Landing Directory Viewer
# ----------------------------------
st.subheader("📂 Landing Directory")

render_directory_view(
    directory=LANDING_DIR,
    title=None,
    session_key="accidents_landing"
)

st.divider()


# ----------------------------------
# Download Controls
# ----------------------------------
st.subheader("⬇️ Download Controls")

col1, col2 = st.columns(2)

with col1:
    if st.button("Download from Kaggle", type="primary", use_container_width=True):

        try:
            with st.spinner("Downloading dataset from Kaggle..."):
                result = download()

            st.success(f"Download status: {result['status']}")
            st.rerun()

        except Exception:
            import traceback
            st.error("Kaggle download failed")
            st.code(traceback.format_exc())


with col2:
    st.info(
        """
        **Kaggle Dataset:**  
        https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents

        If Kaggle credentials are not configured,
        manually download and extract the CSV into:

        `data/landing/accidents/`
        """
    )

st.divider()


# ----------------------------------
# Status Check
# ----------------------------------
files = list(LANDING_DIR.glob("*.csv"))

if files:
    st.success(f"Detected {len(files)} CSV file(s). Ready for ingest.")

    # Optional Preview
    try:
        df = pd.read_csv(files[0], nrows=5)
        st.subheader("🔍 Preview (First 5 Rows)")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.warning(f"Preview failed: {e}")

else:
    st.warning("No CSV files detected in landing directory.")
