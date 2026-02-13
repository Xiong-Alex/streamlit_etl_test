def download():
    """Download accidents CSV"""

def ingest(engine):
    """Load into bronze.accidents"""

def transform(engine):
    """bronze → silver"""

def run_all(engine):
    download()
    ingest(engine)
    transform(engine)
