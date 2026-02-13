from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st


# Hard limit for UI rendering
MAX_PREVIEW_FILES = 20


def _scan_directory(directory: Path) -> pd.DataFrame:
    """
    Pure function.
    Returns sorted dataframe of file metadata.
    """

    files = list(directory.glob("*"))

    if not files:
        return pd.DataFrame()

    rows = []

    for f in files:
        stat = f.stat()
        rows.append({
            "File Name": f.name,
            "Size (KB)": round(stat.st_size / 1024, 2),
            "Last Modified": datetime.fromtimestamp(stat.st_mtime),
        })

    df = pd.DataFrame(rows)
    return df.sort_values("Last Modified", ascending=False)


def render_directory_view(
    directory: Path,
    title: str | None = None,
    session_key: str | None = None,
):
    """
    Simple reusable directory viewer.
    Preview is capped for performance.
    """

    if title:
        st.subheader(title)

    if not directory.exists():
        st.warning(f"Directory does not exist: {directory}")
        return

    df = _scan_directory(directory)

    if df.empty:
        st.info("No files found.")
        return

    total_files = len(df)

    # ----------------------------------
    # Metrics
    # ----------------------------------
    col1, col2 = st.columns(2)

    col1.metric("File Count", f"{total_files:,}")
    col2.metric(
        "Total Size (MB)",
        round(df["Size (KB)"].sum() / 1024, 2)
    )

    # ----------------------------------
    # Limited Preview
    # ----------------------------------
    if total_files > MAX_PREVIEW_FILES:
        st.info(
            f"Showing first {MAX_PREVIEW_FILES:,} of {total_files:,} files."
        )
        df = df.head(MAX_PREVIEW_FILES)

    st.dataframe(df, width="stretch")

    # ----------------------------------
    # Refresh
    # ----------------------------------
    refresh_key = f"refresh_{session_key}" if session_key else None

    if st.button("Refresh Directory", key=refresh_key, width="stretch"):
        st.rerun()
