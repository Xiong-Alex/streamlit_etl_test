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
# BUILD ACCIDENT → STATION MAP
# ==================================
def build(truncate: bool = True) -> dict:
    """
    Populate silver.accident_station_map by mapping
    each accident to its nearest station.

    Args:
        truncate: If True, clears table before rebuild.

    Returns:
        dict with row count and execution time.
    """

    engine = get_engine()

    # ----------------------------------
    # Validate Dependencies
    # ----------------------------------
    validate_table(
        engine,
        "silver.us_accidents",
        not_empty=True,
        required_columns=["accident_id", "geom"],
    )

    validate_table(
        engine,
        "silver.stations",
        not_empty=True,
        required_columns=["station_id", "geom"],
    )

    start_time = time.perf_counter()

    with engine.begin() as conn:

        if truncate:
            logger.info("Truncating silver.accident_station_map")
            conn.execute(text("TRUNCATE TABLE silver.accident_station_map"))

        logger.info("Building accident_station_map (nearest station mapping)")

        conn.execute(text("""
            INSERT INTO silver.accident_station_map (
                accident_id,
                station_id,
                distance_km
            )
            SELECT
                a.accident_id,
                s.station_id,
                ST_Distance(a.geom, s.geom) / 1000.0 AS distance_km
            FROM silver.us_accidents a
            CROSS JOIN LATERAL (
                SELECT station_id, geom
                FROM silver.stations
                ORDER BY a.geom <-> geom
                LIMIT 1
            ) s
            WHERE a.geom IS NOT NULL
            ON CONFLICT (accident_id)
            DO UPDATE SET
                station_id = EXCLUDED.station_id,
                distance_km = EXCLUDED.distance_km;
        """))

    elapsed = time.perf_counter() - start_time

    # ----------------------------------
    # Row Count
    # ----------------------------------
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM silver.accident_station_map")
        ).scalar()

    logger.info(
        f"Accident → Station map built: {count:,} rows "
        f"in {elapsed:.2f} seconds"
    )

    return {
        "rows_mapped": count,
        "seconds": round(elapsed, 2),
    }
