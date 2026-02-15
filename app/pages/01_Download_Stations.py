# ----------------------------------
# Imports
# ----------------------------------
import streamlit as st
import pandas as pd
from pathlib import Path

from pipeline.stations import download
from components.directory_viewer import render_directory_view

# ----------------------------------
# Constants
# ----------------------------------
LANDING_DIR = Path("/data/landing/stations")
LANDING_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------
# Page Config
# ----------------------------------
st.title("Stations: Download to Landing")
st.caption("Download and stage NOAA station metadata")

st.divider()


# ----------------------------------
# Landing Directory Viewer
# ----------------------------------
st.subheader("📂 Landing Directory")

render_directory_view(
    directory=LANDING_DIR,
    title=None,
    session_key="stations_landing"
)

st.divider()


# ----------------------------------
# Controls Section
# ----------------------------------
st.subheader("⬇️ Download Controls")

if st.button("Download Stations", type="primary", use_container_width=True):

    try:
        with st.spinner("Downloading and processing station file..."):
            csv_path = download()

        st.session_state["stations_csv_path"] = str(csv_path)

        st.success("Stations downloaded successfully")
        st.rerun()

    except Exception:
        import traceback
        st.error("Download failed")
        st.code(traceback.format_exc())


# ----------------------------------
# Preview Section
# ----------------------------------
if "stations_csv_path" in st.session_state:

    csv_path = Path(st.session_state["stations_csv_path"])

    if csv_path.exists():

        try:
            df = pd.read_csv(csv_path)

            st.divider()
            st.subheader("🔍 Preview (First 5 Rows)")
            st.dataframe(df.head(), use_container_width=True)

        except Exception as e:
            st.warning(f"Preview failed: {e}")

    else:
        st.info("Downloaded file has been moved or archived.")