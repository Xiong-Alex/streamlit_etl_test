CREATE UNLOGGED TABLE IF NOT EXISTS bronze.stations (
    station_id   TEXT NOT NULL,
    latitude     TEXT,
    longitude    TEXT,
    elevation    TEXT,
    state        TEXT,
    name         TEXT,
    gsn          TEXT,
    hcn          TEXT,
    wmo          TEXT,
    ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bronze_stations_station_id
    ON bronze.stations (station_id);
