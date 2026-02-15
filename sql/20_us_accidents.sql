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
