# ==================================
# Imports
# ==================================
import streamlit as st
from pathlib import Path

# ==================================
# Config
# ==================================
st.set_page_config(page_title="View Logs", layout="wide")

LOG_FILE = Path("logs") / "pipeline.log"

# ==================================
# Header
# ==================================
st.title("📜 Pipeline Logs")
st.caption("Showing last 200 log entries")

# ==================================
# Helper Functions
# ==================================
def read_logs():
    if not LOG_FILE.exists():
        return f"No log file found at: {LOG_FILE.resolve()}"

    lines = LOG_FILE.read_text().splitlines()
    return "\n".join(lines[-200:])

def clear_logs():
    if LOG_FILE.exists():
        LOG_FILE.write_text("")

# ==================================
# Controls
# ==================================
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresh Logs"):
        st.rerun()

with col2:
    if st.button("🗑 Clear Logs"):
        clear_logs()
        st.success("Logs cleared.")
        st.rerun()

# ==================================
# Display
# ==================================
st.divider()

logs = read_logs()
st.code(logs if logs else "Log file is empty.", language="bash")
