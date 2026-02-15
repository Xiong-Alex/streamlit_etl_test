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
# BUILD GOLD: accident_weather
# ==================================
def build(truncate: bool = True) -> dict:
    """
    Build gold.accident_weather fact table.

    Combines:
    - silver.us_accidents
    - silver.accident_station_map
    - silver.weather_daily_pivot
    """

    engine = get_engine()

    # ----------------------------------
    # Validate Dependencies
    # ----------------------------------
    validate_table(engine, "silver.us_accidents", not_empty=True)
    validate_table(engine, "silver.accident_station_map", not_empty=True)
    validate_table(engine, "silver.weather_daily_pivot", not_empty=True)

    start_time = time.perf_counter()

    with engine.begin() as conn:

        if truncate:
            logger.info("Truncating gold.accident_weather")
            conn.execute(text("TRUNCATE TABLE gold.accident_weather"))

        logger.info("Building gold.accident_weather")

        conn.execute(text("""
            INSERT INTO gold.accident_weather (
                accident_id,
                station_id,
                distance_km,
                obs_date,
                severity,
                start_time,
                latitude,
                longitude,
                geom,
                state,
                darkness_level,
                tmax_c,
                tmin_c,
                prcp_mm,
                snow_mm
            )
            SELECT
                a.accident_id,
                m.station_id,
                m.distance_km,
                DATE(a.start_time) AS obs_date,
                a.severity,
                a.start_time,
                a.latitude,
                a.longitude,
                a.geom::GEOMETRY(Point, 4326),
                a.state,
                a.darkness_level,
                w.tmax_c,
                w.tmin_c,
                w.prcp_mm,
                w.snow_mm
            FROM silver.us_accidents a
            JOIN silver.accident_station_map m
                ON a.accident_id = m.accident_id
            LEFT JOIN silver.weather_daily_pivot w
                ON w.station_id = m.station_id
                AND w.obs_date = DATE(a.start_time)
            WHERE a.geom IS NOT NULL
            ON CONFLICT (accident_id) DO NOTHING;
        """))

    elapsed = time.perf_counter() - start_time

    # ----------------------------------
    # Row Count
    # ----------------------------------
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM gold.accident_weather")
        ).scalar()

    logger.info(
        f"Gold accident_weather built: {count:,} rows "
        f"in {elapsed:.2f} seconds"
    )

    return {
        "rows_written": count,
        "seconds": round(elapsed, 2),
    }
