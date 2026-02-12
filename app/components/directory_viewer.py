# ----------------------------------
# Imports
# ----------------------------------
from pathlib import Path
import pandas as pd
import streamlit as st
from datetime import datetime


# ----------------------------------
# Directory Viewer Component
# ----------------------------------
def render_directory_view(title: str, directory: Path):

    st.markdown(f"## {title}")

    if not directory.exists():
        st.warning(f"Directory does not exist: {directory}")
        return

    files = list(directory.glob("*"))

    if not files:
        st.info("No files found.")
        return

    file_data = []

    for f in files:
        stat = f.stat()
        file_data.append({
            "File Name": f.name,
            "Size (KB)": round(stat.st_size / 1024, 2),
            "Last Modified": datetime.fromtimestamp(stat.st_mtime),
        })

    df = pd.DataFrame(file_data).sort_values("Last Modified", ascending=False)

    # Metrics side-by-side
    col1, col2 = st.columns(2)
    col1.metric("File Count", len(df))
    col2.metric("Total Size (MB)", round(df["Size (KB)"].sum() / 1024, 2))

    st.dataframe(df, use_container_width=True)

    if st.button(f"Refresh {title}", key=f"refresh_{title}"):
        st.rerun()
