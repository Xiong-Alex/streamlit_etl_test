from pipeline.stations import run_all as run_stations
from pipeline.weather import run_all as run_weather
from pipeline.accidents import run_all as run_accidents
from pipeline.gold import build as run_gold


def run_full(engine, states: list[str]):
    """
    Full DAG execution.
    """

    run_stations(engine)

    run_weather(engine, states)

    run_accidents(engine)

    run_gold(engine)
