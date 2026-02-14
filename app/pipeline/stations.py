# ----------------------------------
# Imports
# ----------------------------------
from pathlib import Path
import csv
import requests
import pandas as pd
from sqlalchemy import text

from pipeline.validator import validate_table
# DB Connection
from components.db import get_engine

from components.logger import get_logger
logger = get_logger(__name__)


# ----------------------------------
# Constants
# ----------------------------------
BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily"

OUT_DIR = Path("/data/landing/stations")
ARCHIVE_DIR = Path("/data/archive/stations")


# ==================================
# DOWNLOAD
# ==================================
def download() -> Path:
    """
    Download ghcnd-stations.txt and convert to CSV.
    Returns path to generated CSV file.
    """

    engine = get_engine()

    # -----------------------------
    # Validate Bronze Before Transform
    # -----------------------------
    if not validate_table(
        engine,
        "bronze.stations",
        not_empty=False,
    ):
        raise RuntimeError("Bronze table validation failed.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    txt_path = OUT_DIR / "ghcnd-stations.txt"
    csv_path = OUT_DIR / "ghcnd-stations.csv"

    r = requests.get(f"{BASE_URL}/ghcnd-stations.txt", timeout=60)
    r.raise_for_status()
    txt_path.write_bytes(r.content)

    with open(txt_path, "r", encoding="utf-8") as fin, open(
        csv_path, "w", newline="", encoding="utf-8"
    ) as fout:

        writer = csv.writer(fout)

        writer.writerow([
            "station_id",
            "latitude",
            "longitude",
            "elevation",
            "state",
            "name",
            "gsn",
            "hcn",
            "wmo",
        ])

        for line in fin:
            station_id = line[0:11].strip()
            if not station_id:
                continue

            def val(s):
                s = s.strip()
                return s if s else None

            writer.writerow([
                station_id,
                val(line[12:20]),
                val(line[21:30]),
                val(line[31:37]),
                val(line[38:40]),
                val(line[41:71]),
                val(line[72:75]),
                val(line[76:79]),
                val(line[80:85]),
            ])

    txt_path.unlink()

    if not csv_path.exists():
        raise RuntimeError("Stations CSV was not created.")

    return csv_path


# ==================================
# INGEST → BRONZE
# ==================================
def ingest() -> dict:
    """
    Load ghcnd-stations.csv into bronze.stations.
    Moves file to archive after successful load.
    """
    engine = get_engine()



    csv_path = OUT_DIR / "ghcnd-stations.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            "Stations CSV not found. Run download() first."
        )

    df = pd.read_csv(csv_path)
    row_count = len(df)

    if row_count == 0:
        raise ValueError("Stations CSV is empty.")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bronze.stations"))

        df.to_sql(
            name="stations",
            schema="bronze",
            con=conn,
            if_exists="append",
            index=False,
            method="multi"
        )

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / csv_path.name
    csv_path.rename(archive_path)

    return {
        "rows_inserted": row_count,
        "table": "bronze.stations"
    }


# ==================================
# TRANSFORM → SILVER (SQL VERSION)
# ==================================
def transform(truncate: bool = True) -> dict:
    """
    Transform bronze.stations → silver.stations using SQL.
    """

    engine = get_engine()

    # -----------------------------
    # Validate Bronze Before Transform
    # -----------------------------
    if not validate_table(
        engine,
        "bronze.stations",
        not_empty=True,
        required_columns=[
            "station_id",
            "latitude",
            "longitude",
        ],
    ):
        raise RuntimeError("Bronze stations validation failed.")

    # -----------------------------
    # Transform
    # -----------------------------
    with engine.begin() as conn:

        if truncate:
            conn.execute(text("TRUNCATE TABLE silver.stations"))

        conn.execute(text("""
            INSERT INTO silver.stations (
                station_id,
                country_code,
                state,
                name,
                latitude,
                longitude,
                elevation_m,
                is_gsn,
                is_hcn,
                geom
            )
            SELECT
                TRIM(station_id),
                LEFT(TRIM(station_id), 2),
                TRIM(state),
                TRIM(name),
                TRIM(latitude)::DOUBLE PRECISION,
                TRIM(longitude)::DOUBLE PRECISION,
                NULLIF(TRIM(elevation), '')::DOUBLE PRECISION,
                (TRIM(gsn) = 'GSN'),
                (TRIM(hcn) = 'HCN'),
                ST_SetSRID(
                    ST_MakePoint(
                        TRIM(longitude)::DOUBLE PRECISION,
                        TRIM(latitude)::DOUBLE PRECISION
                    ),
                    4326
                )::GEOGRAPHY
            FROM bronze.stations
            WHERE TRIM(station_id) LIKE 'US%'
              AND TRIM(latitude) <> ''
              AND TRIM(longitude) <> ''
            ON CONFLICT (station_id) DO NOTHING;
        """))

    return {
        "rows_written": "Check silver.stations count"
    }



# ==================================
# FULL DATASET LIFECYCLE
# ==================================
def run_all():
    """
    Run download → ingest → transform
    """

    download()
    bronze_result = ingest()
    silver_result = transform()

    return {
        "bronze": bronze_result,
        "silver": silver_result
    }
