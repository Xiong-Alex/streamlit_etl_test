# ----------------------------------
# Imports
# ----------------------------------
import logging
import sys
from pathlib import Path


# ----------------------------------
# Log Directory
# ----------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"


def get_logger(name: str) -> logging.Logger:
    """
    Returns configured logger.

    - Logs to stdout
    - Logs to logs/pipeline.log
    - Prevents duplicate handlers
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # -----------------------------
    # Console Handler
    # -----------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # -----------------------------
    # File Handler
    # -----------------------------
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
