# ==================================
# Imports
# ==================================
from pathlib import Path
from datetime import date
import csv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from sqlalchemy import text


# ==================================
# Constants
# ==================================
BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"

LANDING_DIR = Path("/data/landing/weather")
ARCHIVE_DIR = Path("/data/archive/weather")

LANDING_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ==================================
# DOWNLOAD
# ==================================
def download(engine, states: list[str], start_date=None, end_date=None, max_workers=12):
    """
    Download NOAA .dly files for stations in selected states.
    """

    if not states:
        return {"downloaded": 0}

    # Fetch station_ids
    placeholders = ",".join([f":s{i}" for i in range(len(states))])
    query = text(f"""
        SELECT station_id
        FROM silver.stations
        WHERE state IN ({placeholders})
    """)
    params = {f"s{i}": s for i, s in enumerate(states)}

    station_ids = pd.read_sql(query, engine, params=params)["station_id"].tolist()

    if not station_ids:
        return {"downloaded": 0}

    if start_date is None:
        start_date = date(2015, 1, 1)
    if end_date is None:
        end_date = date.today()

    def download_station(station_id: str):
        out_csv = LANDING_DIR / f"{station_id}.csv"
        if out_csv.exists():
            return

        url = f"{BASE_URL}/{station_id}.dly"
        r = requests.get(url, timeout=60)
        r.raise_for_status()

        with open(out_csv, "w", newline="") as fout:
            writer = csv.writer(fout)

            writer.writerow([
                "station_id",
                "obs_date",
                "element",
                "value",
                "m_flag",
                "q_flag",
                "s_flag",
            ])

            for line in r.text.splitlines():
                station = line[0:11].strip()
                year = int(line[11:15])
                month = int(line[15:17])
                element = line[17:21]

                for day in range(1, 32):
                    base = 21 + (day - 1) * 8
                    value = line[base:base+5].strip()

                    if value == "-9999":
                        continue

                    try:
                        obs_date = date(year, month, day)
                    except ValueError:
                        continue

                    if not (start_date <= obs_date <= end_date):
                        continue

                    writer.writerow([
                        station,
                        obs_date.isoformat(),
                        element,
                        int(value),
                        line[base+5].strip() or None,
                        line[base+6].strip() or None,
                        line[base+7].strip() or None,
                    ])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_station, sid) for sid in station_ids]
        for f in as_completed(futures):
            f.result()

    return {"downloaded": len(station_ids)}


# ==================================
# INGEST → BRONZE
# ==================================
def ingest(engine, files: list[str] | None = None):
    """
    Ingest weather CSV files from landing directory into bronze.weather_daily
    """

    if files is None:
        files = list(LANDING_DIR.glob("*.csv"))

    if not files:
        return {"rows_inserted": 0}

    total_rows = 0

    with engine.begin() as conn:
        for file in files:
            df = pd.read_csv(file)

            total_rows += len(df)

            df.to_sql(
                name="weather_daily",
                schema="bronze",
                con=conn,
                if_exists="append",
                index=False,
                method="multi"
            )

            # Move to archive
            file.rename(ARCHIVE_DIR / file.name)

    return {"rows_inserted": total_rows}


# ==================================
# TRANSFORM → SILVER (SQL)
# ==================================
def transform(engine):
    """
    Transform bronze.weather_daily → silver.weather_daily
    """

    with engine.begin() as conn:

        conn.execute(text("""
            INSERT INTO silver.weather_daily (
                station_id,
                obs_date,
                element,
                value
            )
            SELECT
                station_id,
                obs_date::DATE,
                element,
                value::DOUBLE PRECISION
            FROM bronze.weather_daily
            ON CONFLICT (station_id, obs_date, element)
            DO UPDATE SET value = EXCLUDED.value;
        """))

    return {"status": "silver.weather_daily updated"}


# ==================================
# RUN ALL
# ==================================
def run_all(engine, states: list[str]):
    d = download(engine, states)
    i = ingest(engine)
    t = transform(engine)

    return {
        "download": d,
        "ingest": i,
        "transform": t
    }
