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


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Stations: Download to Landing")


# ----------------------------------
# Directory Viewer
# ----------------------------------
render_directory_view(
    directory=LANDING_DIR,
    title="Landing Directory",
    session_key="stations_landing"
)

st.divider()


# ----------------------------------
# Download Button
# ----------------------------------
if st.button("Download Stations", width="stretch"):

    with st.spinner("Downloading and processing station file..."):
        csv_path = download()

    st.session_state["stations_csv_path"] = str(csv_path)

    st.success(f"Saved to: {csv_path}")


# ----------------------------------
# Preview Section 
# ----------------------------------
if "stations_csv_path" in st.session_state:

    csv_path = Path(st.session_state["stations_csv_path"])

    if csv_path.exists():

        try:
            df = pd.read_csv(csv_path)

            st.subheader("Preview")
            st.dataframe(df.head(), width="stretch")

        except Exception as e:
            st.warning(f"Preview failed: {e}")

    else:
        st.info("Downloaded file has been moved or archived.")
