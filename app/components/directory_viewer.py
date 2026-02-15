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
    Reusable directory viewer with:
    - Metrics
    - Limited preview
    - Refresh button
    - Clear directory button (.gitkeep preserved)
    """

    if title:
        st.subheader(title)

    if not directory.exists():
        st.warning(f"Directory does not exist: {directory}")
        return

    df = _scan_directory(directory)

    if df.empty:
        st.info("No files found.")

    else:
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
                f"Showing first {MAX_PREVIEW_FILES:,} "
                f"of {total_files:,} files."
            )
            df = df.head(MAX_PREVIEW_FILES)

        st.dataframe(df, use_container_width=True)

    # ----------------------------------
    # Controls
    # ----------------------------------
    col1, col2 = st.columns(2)

    refresh_key = f"refresh_{session_key}" if session_key else None
    clear_key = f"clear_{session_key}" if session_key else None

    # 🔄 Refresh
    if col1.button("Refresh Directory", key=refresh_key, use_container_width=True):
        st.rerun()

    # 🧹 Clear (preserve .gitkeep)
    if col2.button("Clear Directory", key=clear_key, use_container_width=True):

        deleted = 0

        for file in directory.glob("*"):
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
                deleted += 1

        st.success(f"Deleted {deleted} file(s). (.gitkeep preserved)")
        st.rerun()
