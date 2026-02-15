# ==================================
# Imports
# ==================================
from pathlib import Path
import time
from sqlalchemy import text

from components.db import get_engine
from pipeline.validators import validate_table
from components.logger import get_logger

from kaggle.api.kaggle_api_extended import KaggleApi

logger = get_logger(__name__)


# ==================================
# Paths
# ==================================
LANDING_DIR = Path("/data/landing/accidents")
ARCHIVE_DIR = Path("/data/archive/accidents")

LANDING_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ==================================
# DOWNLOAD
# ==================================
def download() -> dict:
    """
    Download US Accidents dataset from Kaggle.
    Uses environment variables for authentication.
    """

    dataset = "sobhanmoosavi/us-accidents"

    # Skip if CSV already exists
    if list(LANDING_DIR.glob("*.csv")):
        logger.info("Accidents dataset already exists. Skipping download.")
        return {"status": "exists"}

    logger.info("Downloading accidents dataset from Kaggle")

    api = KaggleApi()
    api.authenticate()

    api.dataset_download_files(
        dataset,
        path=LANDING_DIR,
        unzip=True
    )

    logger.info("Download complete")

    return {"status": "downloaded"}

# ==================================
# INGEST → BRONZE (COPY BASED)
# ==================================
def ingest(truncate: bool = False) -> dict:
    """
    Stream large accident CSV(s) into bronze.us_accidents
    using PostgreSQL COPY (memory safe).
    """

    engine = get_engine()
    files = list(LANDING_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            "No accident CSV files found in landing directory."
        )

    total_rows = 0
    start_time = time.perf_counter()

    # ----------------------------------
    # Optional Truncate
    # ----------------------------------
    if truncate:
        with engine.begin() as conn:
            logger.info("Truncating bronze.us_accidents")
            conn.execute(text("TRUNCATE TABLE bronze.us_accidents"))

    # ----------------------------------
    # COPY Per File (Safe + Resume Friendly)
    # ----------------------------------
    for file in files:
        logger.info(f"COPY ingest started: {file.name}")

        raw_conn = engine.raw_connection()
        try:
            cur = raw_conn.cursor()

            with open(file, "r") as f:
                cur.copy_expert(
                    """
                    COPY bronze.us_accidents
                    FROM STDIN
                    WITH (FORMAT CSV, HEADER TRUE)
                    """,
                    f,
                )

            raw_conn.commit()

            # Fast line count (minus header)
            with open(file, "r") as f:
                row_count = sum(1 for _ in f) - 1

            total_rows += row_count

            # Move to archive AFTER successful commit
            file.rename(ARCHIVE_DIR / file.name)

            logger.info(
                f"Finished ingest {file.name} "
                f"({row_count:,} rows)"
            )

        finally:
            raw_conn.close()

    elapsed = time.perf_counter() - start_time

    # ----------------------------------
    # Post-Ingest Validation
    # ----------------------------------
    validate_table(
        engine,
        "bronze.us_accidents",
        not_empty=True,
        required_columns=[
            "id",
            "start_time",
            "end_time",
            "start_lat",
            "start_lng",
        ],
    )

    logger.info(
        f"Inserted {total_rows:,} rows into bronze.us_accidents "
        f"in {elapsed:.2f} seconds"
    )

    return {
        "rows_inserted": total_rows,
        "seconds": round(elapsed, 2),
    }

# ==================================
# TRANSFORM → SILVER
# ==================================
def transform(
    truncate: bool = False,
    states: list[str] | None = None,
    restrict_to_weather_range: bool = True,
) -> dict:
    """
    Transform bronze.us_accidents → silver.us_accidents
    """

    engine = get_engine()

    # ----------------------------------
    # Pre-Validation
    # ----------------------------------
    validate_table(
        engine,
        "bronze.us_accidents",
        not_empty=True,
        required_columns=[
            "id",
            "start_time",
            "end_time",
            "start_lat",
            "start_lng",
        ],
    )

    start_time_perf = time.perf_counter()

    # ----------------------------------
    # Transaction Block
    # ----------------------------------
    with engine.begin() as conn:

        # ----------------------------------
        # Optional Truncate
        # ----------------------------------
        if truncate:
            logger.info("Truncating silver.us_accidents")
            conn.execute(text("TRUNCATE TABLE silver.us_accidents"))

        # ----------------------------------
        # Build Dynamic Filters
        # ----------------------------------
        filters = ["start_lat IS NOT NULL", "start_lng IS NOT NULL"]
        params = {}

        # State Filter
        if states:
            placeholders = ",".join(
                [f":s{i}" for i in range(len(states))]
            )
            filters.append(f"state IN ({placeholders})")
            params.update({f"s{i}": s for i, s in enumerate(states)})

        # Weather Date Restriction
        if restrict_to_weather_range:
            weather_result = conn.execute(text("""
                SELECT
                    MIN(obs_date) AS min_date,
                    MAX(obs_date) AS max_date
                FROM silver.weather_daily
            """)).fetchone()

            if weather_result and weather_result[0] and weather_result[1]:
                min_date, max_date = weather_result

                filters.append(
                    "start_time::DATE BETWEEN :min_date AND :max_date"
                )
                params["min_date"] = min_date
                params["max_date"] = max_date

                logger.info(
                    f"Restricting to weather range: "
                    f"{min_date} → {max_date}"
                )
            else:
                logger.warning(
                    "Weather range not found. Skipping restriction."
                )

        where_clause = " AND ".join(filters)

        # ----------------------------------
        # Execute Insert
        # ----------------------------------
        insert_sql = text(f"""
            INSERT INTO silver.us_accidents (
                accident_id,
                severity,
                start_time,
                end_time,
                duration_minutes,
                latitude,
                longitude,
                city,
                county,
                state,
                zipcode,
                weather_time,
                temperature_f,
                wind_chill_f,
                humidity_pct,
                pressure_in,
                visibility_mi,
                wind_speed_mph,
                precipitation_in,
                weather_condition,
                is_amenity,
                is_bump,
                is_crossing,
                is_give_way,
                is_junction,
                is_no_exit,
                is_railway,
                is_roundabout,
                is_station,
                is_stop,
                is_traffic_calming,
                is_traffic_signal,
                is_turning_loop,
                darkness_level,
                geom
            )
            SELECT
                id,
                severity::SMALLINT,
                start_time::TIMESTAMPTZ,
                end_time::TIMESTAMPTZ,
                EXTRACT(EPOCH FROM 
                    (end_time::TIMESTAMPTZ - start_time::TIMESTAMPTZ)
                ) / 60,
                start_lat,
                start_lng,
                city,
                county,
                state,
                zipcode,
                weather_timestamp::TIMESTAMPTZ,
                temperature_f,
                wind_chill_f,
                humidity_pct,
                pressure_in,
                visibility_mi,
                wind_speed_mph,
                precipitation_in,
                weather_condition,
                amenity,
                bump,
                crossing,
                give_way,
                junction,
                no_exit,
                railway,
                roundabout,
                station,
                stop,
                traffic_calming,
                traffic_signal,
                turning_loop,
                CASE
                    WHEN sunrise_sunset = 'Night' THEN 3
                    WHEN civil_twilight = 'Night' THEN 2
                    WHEN nautical_twilight = 'Night' THEN 1
                    ELSE 0
                END,
                ST_SetSRID(
                    ST_MakePoint(start_lng, start_lat),
                    4326
                )::GEOMETRY(Point, 4326)
            FROM bronze.us_accidents
            WHERE {where_clause}
            ON CONFLICT (accident_id) DO NOTHING
        """)

        result = conn.execute(insert_sql, params)

        # ⚠️ rowcount with INSERT + ON CONFLICT can be unreliable in PG
        rows_written = result.rowcount if result.rowcount else 0

    # ----------------------------------
    # Post Validation
    # ----------------------------------
    validate_table(engine, "silver.us_accidents", not_empty=True)

    elapsed = time.perf_counter() - start_time_perf

    logger.info(
        f"Transformed {rows_written:,} rows "
        f"in {elapsed:.2f} sec"
    )

    return {
        "rows_written": rows_written,
        "seconds": round(elapsed, 2),
    }



# ==================================
# RUN ALL
# ==================================
def run_all():
    """
    Full accident lifecycle:
        download → ingest → transform
    """

    download()
    bronze = ingest()
    silver = transform()

    return {
        "bronze": bronze,
        "silver": silver,
    }
