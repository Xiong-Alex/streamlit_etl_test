CREATE UNLOGGED TABLE IF NOT EXISTS silver.accident_station_map (
    accident_id TEXT PRIMARY KEY,
    station_id  TEXT NOT NULL,
    distance_km DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_accident_station_station
    ON silver.accident_station_map (station_id);
