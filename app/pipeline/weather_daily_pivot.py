# ==================================
# Imports
# ==================================
import time
from sqlalchemy import text

from components.db import get_engine
from pipeline.validators import validate_table
from components.logger import get_logger


logger = get_logger(__name__)


# ==================================
# BUILD / REFRESH WEATHER PIVOT
# ==================================
def build(concurrent: bool = False) -> dict:
    """
    Refresh silver.weather_daily_pivot materialized view.

    Args:
        concurrent: If True, uses CONCURRENTLY (requires unique index).

    Returns:
        dict with row count and execution time.
    """

    engine = get_engine()

    validate_table(
        engine,
        "silver.weather_daily",
        not_empty=True,
        required_columns=[
            "station_id",
            "obs_date",
            "element",
            "value",
        ],
    )

    start_time = time.perf_counter()

    logger.info("Refreshing silver.weather_daily_pivot")

    refresh_sql = (
        "REFRESH MATERIALIZED VIEW CONCURRENTLY silver.weather_daily_pivot"
        if concurrent
        else
        "REFRESH MATERIALIZED VIEW silver.weather_daily_pivot"
    )

    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(refresh_sql))

    elapsed = time.perf_counter() - start_time

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM silver.weather_daily_pivot")
        ).scalar()

    logger.info(
        f"Weather pivot refreshed: {count:,} rows "
        f"in {elapsed:.2f} seconds"
    )

    return {
        "rows_refreshed": count,
        "seconds": round(elapsed, 2),
    }
