# ----------------------------------
# Imports
# ----------------------------------
import time
import os
from pathlib import Path

import streamlit as st
from sqlalchemy import text

from components.db import get_engine
from components.table_explorer import render_table_explorer
from components.directory_viewer import render_directory_view


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Accidents Bronze Ingest")


# ----------------------------------
# Paths
# ----------------------------------
LANDING_DIR = Path("/data/landing/accidents")
ARCHIVE_DIR = Path("/data/archive/accidents")

LANDING_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------
# Config
# ----------------------------------
CSV_PATH = LANDING_DIR / "US_Accidents_March23.csv"
engine = get_engine()


# ----------------------------------
# Landing Directory View
# ----------------------------------
render_directory_view("Landing Directory", LANDING_DIR)

st.divider()


# ----------------------------------
# Ingest Controls
# ----------------------------------
st.subheader("Ingest Controls")

truncate_before = st.checkbox(
    "Truncate bronze.us_accidents before ingest",
    value=False,
)

if not CSV_PATH.exists():
    st.warning("US_Accidents_March23.csv not found in landing directory.")
else:
    st.metric("File Size (MB)", round(os.path.getsize(CSV_PATH) / (1024 * 1024), 2))


if st.button("Run COPY Ingest", use_container_width=True):

    if not CSV_PATH.exists():
        st.error("CSV file not found.")
        st.stop()

    start_time = time.perf_counter()

    try:
        with engine.begin() as conn:

            if truncate_before:
                conn.execute(text("TRUNCATE TABLE bronze.us_accidents;"))
                st.info("bronze.us_accidents truncated.")

            raw = conn.connection
            cur = raw.cursor()

            # Performance knobs
            cur.execute("SET synchronous_commit = OFF;")
            cur.execute("SET maintenance_work_mem = '1GB';")
            cur.execute("SET work_mem = '256MB';")

            file_size = os.path.getsize(CSV_PATH)
            progress = st.progress(0)

            with open(CSV_PATH, "rb") as f:

                class ProgressFile:
                    def __init__(self, file):
                        self.file = file
                        self.bytes_read = 0

                    def read(self, size):
                        data = self.file.read(size)
                        self.bytes_read += len(data)
                        progress.progress(
                            min(self.bytes_read / file_size, 1.0)
                        )
                        return data

                wrapped_file = ProgressFile(f)

                cur.copy_expert(
                    """
                    COPY bronze.us_accidents
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        HEADER TRUE,
                        DELIMITER ',',
                        QUOTE '"'
                    )
                    """,
                    wrapped_file
                )

            raw.commit()
            cur.close()

        elapsed = time.perf_counter() - start_time

        # Row count
        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM bronze.us_accidents")
            )
            total_rows = result.scalar()

        st.success("Accidents COPY complete")
        st.write(f"Rows: {total_rows:,}")
        st.write(f"Time: {elapsed:.2f} sec")
        st.write(f"Rows/sec: {int(total_rows / elapsed):,}")

        # Move to archive
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        CSV_PATH.rename(ARCHIVE_DIR / CSV_PATH.name)

        st.rerun()

    except Exception as e:
        st.error(f"Ingest failed: {e}")


# ----------------------------------
# Bronze Table Explorer
# ----------------------------------
st.divider()

render_table_explorer(
    table_name="bronze.us_accidents",
    session_key="bronze_accidents",
    metric_label="Bronze Accident Rows",
    allow_truncate=True,
)
