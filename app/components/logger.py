# ----------------------------------
# Imports
# ----------------------------------
import logging
import sys
from pathlib import Path


# ----------------------------------
# Log Directory (Container-Safe)
# ----------------------------------
# In Docker:
#   WORKDIR = /app
#   logs mounted at /app/logs
#
# Locally:
#   Runs relative to project root
#
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.

    Features:
    - Logs to stdout (Docker console)
    - Logs to logs/pipeline.log
    - Prevents duplicate handlers
    - Safe for repeated imports
    """

    logger = logging.getLogger(name)

    # Prevent duplicate handlers when Streamlit reruns
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent double logging

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ----------------------------------
    # Console Handler (Docker logs)
    # ----------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ----------------------------------
    # File Handler (Persistent logs)
    # ----------------------------------
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
