from pipeline.stations import run_all as run_stations
from pipeline.weather import run_all as run_weather
from pipeline.accidents import run_all as run_accidents
from app.pipeline.accident_weather import build as run_gold

from pipeline.validator import validate_table
from components.db import get_engine


def run_full(states: list[str]):
    """
    Full DAG execution with validation.
    """

    engine = get_engine()

    # -----------------------------
    # Stations
    # -----------------------------
    run_stations()

    if not validate_table(
        engine,
        "silver.stations",
        not_empty=True,
        required_columns=[
            "station_id",
            "latitude",
            "longitude",
            "geom",
        ],
    ):
        raise RuntimeError("Silver stations validation failed — aborting.")

    # -----------------------------
    # Weather
    # -----------------------------
    run_weather(states)

    if not validate_table(
        engine,
        "silver.weather",
        not_empty=True,
        required_columns=[
            "station_id",
            "date",
            "tmin",
            "tmax",
        ],
    ):
        raise RuntimeError("Silver weather validation failed — aborting.")

    # -----------------------------
    # Accidents
    # -----------------------------
    run_accidents()

    if not validate_table(
        engine,
        "silver.accidents",
        not_empty=True,
        required_columns=[
            "id",
            "start_time",
            "latitude",
            "longitude",
        ],
    ):
        raise RuntimeError("Silver accidents validation failed — aborting.")

    # -----------------------------
    # Gold
    # -----------------------------
    run_gold()

    if not validate_table(
        engine,
        "gold.analytics",
        not_empty=True,
    ):
        raise RuntimeError("Gold build failed — no data present.")

    return {"status": "success"}
