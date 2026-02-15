-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- SCHEMAS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ============================================================
-- BRONZE: STATIONS (RAW)
-- ============================================================

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

-- ============================================================
-- SILVER: STATIONS (CLEAN + GEOSPATIAL)
-- ============================================================

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

-- ============================================================
-- BRONZE: WEATHER DAILY (RAW)
-- ============================================================

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

-- ============================================================
-- SILVER: WEATHER DAILY (CLEAN)
-- ============================================================

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

-- ============================================================
-- BRONZE: ACCIDENTS (RAW)
-- ============================================================

CREATE UNLOGGED TABLE IF NOT EXISTS bronze.us_accidents (
    id                      TEXT PRIMARY KEY,
    source                  TEXT,
    severity                INTEGER,
    start_time              TIMESTAMP,
    end_time                TIMESTAMP,
    start_lat               DOUBLE PRECISION,
    start_lng               DOUBLE PRECISION,
    end_lat                 DOUBLE PRECISION,
    end_lng                 DOUBLE PRECISION,
    distance_mi             DOUBLE PRECISION,
    description             TEXT,
    street                  TEXT,
    city                    TEXT,
    county                  TEXT,
    state                   CHAR(2),
    zipcode                 TEXT,
    country                 CHAR(2),
    timezone                TEXT,
    airport_code            TEXT,
    weather_timestamp       TIMESTAMP,
    temperature_f           DOUBLE PRECISION,
    wind_chill_f            DOUBLE PRECISION,
    humidity_pct            DOUBLE PRECISION,
    pressure_in             DOUBLE PRECISION,
    visibility_mi           DOUBLE PRECISION,
    wind_direction          TEXT,
    wind_speed_mph          DOUBLE PRECISION,
    precipitation_in        DOUBLE PRECISION,
    weather_condition       TEXT,
    amenity                 BOOLEAN,
    bump                    BOOLEAN,
    crossing                BOOLEAN,
    give_way                BOOLEAN,
    junction                BOOLEAN,
    no_exit                 BOOLEAN,
    railway                 BOOLEAN,
    roundabout              BOOLEAN,
    station                 BOOLEAN,
    stop                    BOOLEAN,
    traffic_calming         BOOLEAN,
    traffic_signal          BOOLEAN,
    turning_loop            BOOLEAN,
    sunrise_sunset          TEXT,
    civil_twilight          TEXT,
    nautical_twilight       TEXT,
    astronomical_twilight   TEXT
);

-- ============================================================
-- SILVER: ACCIDENTS (CLEAN + GEOSPATIAL)
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.us_accidents (
    accident_id            TEXT PRIMARY KEY,
    severity               SMALLINT NOT NULL,
    start_time             TIMESTAMPTZ NOT NULL,
    end_time               TIMESTAMPTZ,
    duration_minutes       INTEGER, 
    latitude               DOUBLE PRECISION NOT NULL,
    longitude              DOUBLE PRECISION NOT NULL,
    
    city                   TEXT,
    county                 TEXT,
    state                  CHAR(2) NOT NULL,
    zipcode                TEXT,
    weather_time           TIMESTAMPTZ,

    temperature_f          DOUBLE PRECISION,
    wind_chill_f           DOUBLE PRECISION,
    humidity_pct           DOUBLE PRECISION,
    pressure_in            DOUBLE PRECISION,
    visibility_mi          DOUBLE PRECISION,
    wind_speed_mph         DOUBLE PRECISION,
    precipitation_in       DOUBLE PRECISION,
    weather_condition      TEXT,

    is_amenity             BOOLEAN,
    is_bump                BOOLEAN,
    is_crossing            BOOLEAN,
    is_give_way            BOOLEAN,
    is_junction            BOOLEAN,
    is_no_exit             BOOLEAN,
    is_railway             BOOLEAN,
    is_roundabout          BOOLEAN,
    is_station             BOOLEAN,
    is_stop                BOOLEAN,
    is_traffic_calming     BOOLEAN,
    is_traffic_signal      BOOLEAN,
    is_turning_loop        BOOLEAN,
    darkness_level         SMALLINT,

    geom                   GEOGRAPHY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_silver_accidents_geom
    ON silver.us_accidents USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_silver_accidents_state_time
    ON silver.us_accidents (state, start_time);

-- ============================================================
-- SILVER: ACCIDENT → STATION MAP
-- ============================================================

CREATE UNLOGGED TABLE IF NOT EXISTS silver.accident_station_map (
    accident_id TEXT PRIMARY KEY,
    station_id  TEXT NOT NULL,
    distance_km DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_accident_station_station
    ON silver.accident_station_map (station_id);

-- ============================================================
-- GOLD: WEATHER + ACCIDENT
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.accident_weather (
    accident_id        TEXT PRIMARY KEY,
    station_id         TEXT NOT NULL,
    distance_km        DOUBLE PRECISION,
    obs_date           DATE NOT NULL,

    -- Accident
    severity           SMALLINT,
    start_time         TIMESTAMPTZ,
    latitude           DOUBLE PRECISION,
    longitude          DOUBLE PRECISION,
    geom               GEOMETRY(Point, 4326) NOT NULL, -- added to help improve mapping
    state              CHAR(2),
    darkness_level     SMALLINT,

    -- Weather (Metric Explicit)
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

-- ============================================================
-- SILVER: WEATHER DAILY PIVOT (PRE-AGGREGATED)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS silver.weather_daily_pivot AS
SELECT
    station_id,
    obs_date,
    MAX(value) FILTER (WHERE element = 'TMAX') AS tmax_c,
    MAX(value) FILTER (WHERE element = 'TMIN') AS tmin_c,
    MAX(value) FILTER (WHERE element = 'PRCP') AS prcp_mm,
    MAX(value) FILTER (WHERE element = 'SNOW') AS snow_mm
FROM silver.weather_daily
GROUP BY station_id, obs_date;

CREATE INDEX IF NOT EXISTS idx_weather_pivot_station_date
ON silver.weather_daily_pivot (station_id, obs_date);