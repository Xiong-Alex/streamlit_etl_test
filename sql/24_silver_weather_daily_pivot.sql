-- ============================================================
-- MATERIALIZED VIEW: silver.weather_daily_pivot
-- Purpose:
--   Pre-aggregated daily weather metrics per station.
--   Converts row-based elements (TMAX, TMIN, PRCP, SNOW)
--   into a wide analytical format.
--
-- Depends On:
--   silver.weather_daily
--
-- Required For:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY
--   → Requires UNIQUE index with no WHERE clause
-- ============================================================


-- ------------------------------------------------------------
-- Drop legacy non-unique index (if exists)
-- ------------------------------------------------------------
DROP INDEX IF EXISTS silver.idx_weather_pivot_station_date;


-- ------------------------------------------------------------
-- Create / Replace Materialized View
-- ------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS silver.weather_daily_pivot AS
SELECT
    station_id,
    obs_date,

    -- Temperature (°C)
    MAX(value) FILTER (WHERE element = 'TMAX') AS tmax_c,
    MAX(value) FILTER (WHERE element = 'TMIN') AS tmin_c,

    -- Precipitation (mm)
    MAX(value) FILTER (WHERE element = 'PRCP') AS prcp_mm,

    -- Snow (mm)
    MAX(value) FILTER (WHERE element = 'SNOW') AS snow_mm

FROM silver.weather_daily
GROUP BY station_id, obs_date;


-- ------------------------------------------------------------
-- REQUIRED UNIQUE INDEX
-- (Needed for CONCURRENT refresh)
-- ------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS idx_weather_pivot_unique
    ON silver.weather_daily_pivot (station_id, obs_date);
