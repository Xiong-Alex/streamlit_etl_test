CREATE UNLOGGED TABLE IF NOT EXISTS bronze.weather_daily (
    station_id   TEXT NOT NULL,
    obs_date     TEXT NOT NULL,
    element      TEXT NOT NULL,
    value        INTEGER,
    m_flag       TEXT,
    q_flag       TEXT,
    s_flag       TEXT,
    ingested_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bronze_weather_station
    ON bronze.weather_daily (station_id);

CREATE INDEX IF NOT EXISTS idx_bronze_weather_date
    ON bronze.weather_daily (obs_date);

CREATE INDEX IF NOT EXISTS idx_bronze_weather_element
    ON bronze.weather_daily (element);
