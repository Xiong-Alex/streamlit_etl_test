# DB Connection
from components.db import get_engine

def download():
    """Download accidents CSV"""

def ingest():
    engine = get_engine()
    """Load into bronze.accidents"""

def transform():
    engine = get_engine()

    """bronze → silver"""

def run_all():
    download()
    ingest()
    transform()
