CREATE TABLE IF NOT EXISTS silver.stations (
    station_id       TEXT PRIMARY KEY,
    country_code     CHAR(2) NOT NULL,
    state            CHAR(2),
    name             TEXT,
    latitude         DOUBLE PRECISION NOT NULL,
    longitude        DOUBLE PRECISION NOT NULL,
    elevation_m      DOUBLE PRECISION,
    is_gsn           BOOLEAN,
    is_hcn           BOOLEAN,
    geom             GEOGRAPHY(Point, 4326),
    created_at       TIMESTAMPTZ DEFAULT now(),
    last_updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_silver_stations_lat_lon
    ON silver.stations (latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_silver_stations_geom
    ON silver.stations USING GIST (geom);
