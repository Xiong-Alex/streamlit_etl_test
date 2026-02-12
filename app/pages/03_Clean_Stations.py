# ----------------------------------
# Imports
# ----------------------------------
import time
import streamlit as st
from sqlalchemy import create_engine, text

from components.table_explorer import render_table_explorer


# ----------------------------------
# Page Title
# ----------------------------------
st.title("Transform Stations: Bronze → Silver")


# ----------------------------------
# DB Connection (SQLAlchemy)
# ----------------------------------
engine = create_engine(
    "postgresql+psycopg2://postgres:postgres@postgres:5432/etl_db"
)


def get_connection():
    return engine.connect()


def truncate_silver_table():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE silver.stations;"))


# ----------------------------------
# Transform Controls
# ----------------------------------
st.subheader("Transform Controls")

truncate_silver = st.checkbox(
    "Truncate silver.stations before transform",
    value=False
)


if st.button("Run Bronze → Silver Transform", use_container_width=True):

    start_time = time.perf_counter()

    try:
        with engine.begin() as conn:

            if truncate_silver:
                conn.execute(text("TRUNCATE TABLE silver.stations;"))
                st.info("silver.stations truncated.")

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
                SELECT DISTINCT
                    TRIM(station_id) AS station_id,

                    SUBSTRING(TRIM(station_id) FROM 1 FOR 2) AS country_code,

                    TRIM(state) AS state,
                    TRIM(name) AS name,

                    TRIM(latitude)::DOUBLE PRECISION AS latitude,
                    TRIM(longitude)::DOUBLE PRECISION AS longitude,
                    NULLIF(TRIM(elevation), '')::DOUBLE PRECISION AS elevation_m,

                    (TRIM(gsn) = 'GSN') AS is_gsn,
                    (TRIM(hcn) = 'HCN') AS is_hcn,

                    ST_SetSRID(
                        ST_MakePoint(
                            TRIM(longitude)::DOUBLE PRECISION,
                            TRIM(latitude)::DOUBLE PRECISION
                        ),
                        4326
                    )::GEOGRAPHY

                FROM bronze.stations

                WHERE station_id LIKE 'US%'
                  AND TRIM(state) <> ''
                  AND TRIM(latitude) <> ''
                  AND TRIM(longitude) <> ''

                ON CONFLICT (station_id) DO NOTHING
            """))

        elapsed = time.perf_counter() - start_time

        st.success("Transform complete")
        st.write(f"Time: {elapsed:.2f} seconds")

        st.rerun()

    except Exception as e:
        st.error(f"Transform failed: {e}")


# ----------------------------------
# Bronze Explorer
# ----------------------------------
st.markdown("## Bronze Layer")

render_table_explorer(
    table_name="bronze.stations",
    session_key="bronze_stations_transform",
    metric_label="Bronze Rows",
    allow_truncate=False,
)


# ----------------------------------
# Silver Explorer
# ----------------------------------
st.markdown("## Silver Layer")

render_table_explorer(
    table_name="silver.stations",
    session_key="silver_stations",
    metric_label="Silver Rows",
    allow_truncate=True,
    truncate_sql="TRUNCATE TABLE silver.stations;",
)

