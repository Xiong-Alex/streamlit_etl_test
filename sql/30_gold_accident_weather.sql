CREATE TABLE IF NOT EXISTS gold.accident_weather (
    accident_id        TEXT PRIMARY KEY,
    station_id         TEXT NOT NULL,
    distance_km        DOUBLE PRECISION,
    obs_date           DATE NOT NULL,
    severity           SMALLINT,
    start_time         TIMESTAMPTZ,
    latitude           DOUBLE PRECISION,
    longitude          DOUBLE PRECISION,
    geom               GEOMETRY(Point, 4326) NOT NULL,
    state              CHAR(2),
    darkness_level     SMALLINT,
    tmax_c             DOUBLE PRECISION,
    tmin_c             DOUBLE PRECISION,
    prcp_mm            DOUBLE PRECISION,
    snow_mm            DOUBLE PRECISION,
    created_at         TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gold_obs_date
    ON gold.accident_weather (obs_date);

CREATE INDEX IF NOT EXISTS idx_gold_state_date
    ON gold.accident_weather (state, obs_date);

CREATE INDEX IF NOT EXISTS idx_gold_station
    ON gold.accident_weather (station_id);

CREATE INDEX IF NOT EXISTS idx_gold_darkness
    ON gold.accident_weather (darkness_level);
