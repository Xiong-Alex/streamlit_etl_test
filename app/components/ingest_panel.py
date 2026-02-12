# ----------------------------------
# Imports
# ----------------------------------
import time
import shutil
import threading
from pathlib import Path
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import pandas as pd
from sqlalchemy import text

from components.db import get_engine


# ----------------------------------
# Smart Ingest Panel (Auto Thread Aware)
# ----------------------------------
def render_ingest_panel(
    dataset_name: str,
    landing_dir: Path,
    archive_dir: Path,
    table_name: str,
    copy_sql: str,
    session_key: str,
    max_threads: int = 20,
    default_threads: int = 4,
):

    engine = get_engine()

    # ----------------------------------
    # Session State Tracking
    # ----------------------------------
    file_key = f"{session_key}_file"
    time_key = f"{session_key}_time"
    rows_key = f"{session_key}_rows"

    for key in (file_key, time_key, rows_key):
        if key not in st.session_state:
            st.session_state[key] = None

    # ----------------------------------
    # Discover Landing Files
    # ----------------------------------
    landing_files = sorted(landing_dir.glob("*.csv"))
    total_files = len(landing_files)

    # ----------------------------------
    # Landing Preview
    # ----------------------------------
    if total_files > 0:
        st.markdown("**Landing File Preview**")
        try:
            df_preview = pd.read_csv(landing_files[0], nrows=10)
            st.dataframe(df_preview, use_container_width=True)
            st.caption(f"{total_files} file(s) ready for ingest")
        except Exception as e:
            st.warning(f"Preview failed: {e}")
    else:
        if st.session_state[file_key]:
            st.success(
                f"Last ingest: {st.session_state[file_key]} "
                f"({st.session_state[rows_key]:,} rows)"
            )
        else:
            st.warning("No landing files detected.")
        return

    # ----------------------------------
    # Smart Thread Controls
    # ----------------------------------
    if total_files == 1:
        thread_count = 1
        st.info("Single file detected — threading disabled.")
    else:
        max_allowed = min(total_files, max_threads)

        thread_count = st.slider(
            "Worker Threads",
            min_value=1,
            max_value=max_allowed,
            value=min(default_threads, max_allowed),
            key=f"threads_{session_key}",
        )

    truncate_before = st.checkbox(
        f"Truncate {table_name} before ingest",
        value=False,
        key=f"truncate_{session_key}",
    )

    # ----------------------------------
    # Ingest Button
    # ----------------------------------
    if st.button(f"Ingest {dataset_name}", use_container_width=True):

        start_time = time.perf_counter()

        try:
            # Optional truncate
            if truncate_before:
                with engine.begin() as conn:
                    conn.execute(text(f"TRUNCATE TABLE {table_name};"))
                st.info(f"{table_name} truncated.")

            # Refresh files at execution time
            files = sorted(landing_dir.glob("*.csv"))
            total_files = len(files)

            if total_files == 0:
                st.warning("No files found at execution time.")
                return

            # ----------------------------------
            # SINGLE FILE PATH (No threading)
            # ----------------------------------
            if total_files == 1:

                csv_path = files[0]

                raw_conn = engine.raw_connection()
                cur = raw_conn.cursor()
                cur.execute("SET synchronous_commit = OFF;")

                with open(csv_path, "r") as f:
                    cur.copy_expert(copy_sql, f)

                raw_conn.commit()
                cur.close()
                raw_conn.close()

                archive_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(csv_path, archive_dir / csv_path.name)

                processed_files = 1

            # ----------------------------------
            # MULTI FILE PATH (Threaded)
            # ----------------------------------
            else:

                file_queue = Queue()
                for f in files:
                    file_queue.put(f)

                state = {"processed": 0}
                lock = threading.Lock()
                progress_bar = st.progress(0)

                def worker():
                    raw_conn = engine.raw_connection()
                    cur = raw_conn.cursor()
                    cur.execute("SET synchronous_commit = OFF;")

                    while True:
                        try:
                            csv_path = file_queue.get_nowait()
                        except:
                            break

                        try:
                            with open(csv_path, "r") as f:
                                cur.copy_expert(copy_sql, f)

                            raw_conn.commit()
                            shutil.move(csv_path, archive_dir / csv_path.name)

                            with lock:
                                state["processed"] += 1
                                progress_bar.progress(
                                    state["processed"] / total_files
                                )

                        except Exception as e:
                            raw_conn.rollback()
                            st.error(f"Error on {csv_path.name}: {e}")

                    cur.close()
                    raw_conn.close()

                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = [executor.submit(worker) for _ in range(thread_count)]
                    for f in futures:
                        f.result()

                processed_files = state["processed"]

            # ----------------------------------
            # Post-Ingest Stats
            # ----------------------------------
            with engine.begin() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                total_rows = result.scalar()

            elapsed = time.perf_counter() - start_time

            st.session_state[file_key] = f"{processed_files} file(s)"
            st.session_state[time_key] = time.strftime("%Y-%m-%d %H:%M:%S")
            st.session_state[rows_key] = total_rows

            st.success("Ingest complete")
            st.write(f"Files processed: {processed_files}")
            st.write(f"Rows in table: {total_rows:,}")
            st.write(f"Time: {elapsed:.2f} sec")

            st.rerun()

        except Exception as e:
            st.error(f"Ingest failed: {e}")
