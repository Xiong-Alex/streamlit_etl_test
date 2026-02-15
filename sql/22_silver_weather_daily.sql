CREATE TABLE IF NOT EXISTS silver.weather_daily (
    station_id    TEXT NOT NULL,
    obs_date      DATE NOT NULL,
    element       TEXT NOT NULL,
    value         DOUBLE PRECISION,
    created_at    TIMESTAMPTZ DEFAULT now(),
    last_updated  TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (station_id, obs_date, element)
);

CREATE INDEX IF NOT EXISTS idx_silver_weather_station_date
    ON silver.weather_daily (station_id, obs_date);

CREATE INDEX IF NOT EXISTS idx_silver_weather_element
    ON silver.weather_daily (element);

CREATE INDEX IF NOT EXISTS idx_silver_weather_date_only
    ON silver.weather_daily (obs_date);
