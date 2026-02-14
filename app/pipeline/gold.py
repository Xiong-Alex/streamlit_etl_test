# DB Connection
from components.db import get_engine

def build():
    """
    Create gold tables:
    - accident_weather_summary
    - accident_stats_by_state
    - etc.
    """
