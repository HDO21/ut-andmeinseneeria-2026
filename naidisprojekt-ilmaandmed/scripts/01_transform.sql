TRUNCATE TABLE
    mart.daily_weather_summary,
    mart.fact_weather_forecast,
    mart.dim_location;

INSERT INTO mart.dim_location (
    location_id,
    location_name,
    country,
    latitude,
    longitude
)
SELECT DISTINCT
    location_id,
    location_name,
    'Eesti' AS country,
    latitude,
    longitude
FROM staging.weather_hourly_raw
ORDER BY location_id;

INSERT INTO mart.fact_weather_forecast (
    run_id,
    location_id,
    forecast_time,
    forecast_date,
    temperature_c,
    precipitation_mm,
    wind_speed_ms,
    fetched_at
)
SELECT
    run_id,
    location_id,
    forecast_time,
    forecast_time::date AS forecast_date,
    temperature_c,
    precipitation_mm,
    wind_speed_ms,
    fetched_at
FROM staging.weather_hourly_raw;

INSERT INTO mart.daily_weather_summary (
    run_id,
    location_id,
    location_name,
    forecast_date,
    forecast_hours,
    avg_temp_c,
    max_temp_c,
    total_precipitation_mm,
    max_wind_speed_ms,
    hours_with_precipitation,
    weather_risk_level
)
SELECT
    f.run_id,
    f.location_id,
    l.location_name,
    f.forecast_date,
    COUNT(*)::integer AS forecast_hours,
    ROUND(AVG(f.temperature_c), 2) AS avg_temp_c,
    MAX(f.temperature_c) AS max_temp_c,
    ROUND(SUM(COALESCE(f.precipitation_mm, 0)), 2) AS total_precipitation_mm,
    MAX(f.wind_speed_ms) AS max_wind_speed_ms,
    SUM(CASE WHEN COALESCE(f.precipitation_mm, 0) > 0 THEN 1 ELSE 0 END)::integer AS hours_with_precipitation,
    CASE
        WHEN SUM(COALESCE(f.precipitation_mm, 0)) >= 10
          OR MAX(COALESCE(f.wind_speed_ms, 0)) >= 14
            THEN 'Kõrgem tähelepanu'
        WHEN SUM(COALESCE(f.precipitation_mm, 0)) >= 2
          OR MAX(COALESCE(f.wind_speed_ms, 0)) >= 8
            THEN 'Mõõdukas tähelepanu'
        ELSE 'Tavaline'
    END AS weather_risk_level
FROM mart.fact_weather_forecast AS f
INNER JOIN mart.dim_location AS l
    ON f.location_id = l.location_id
GROUP BY
    f.run_id,
    f.location_id,
    l.location_name,
    f.forecast_date;

CREATE OR REPLACE VIEW mart.latest_pipeline_run AS
SELECT
    run_id,
    fetched_at,
    source_name,
    forecast_days,
    status,
    message
FROM staging.pipeline_runs
WHERE status = 'success'
ORDER BY fetched_at DESC
LIMIT 1;

CREATE OR REPLACE VIEW mart.latest_weather_forecast AS
SELECT f.*
FROM mart.fact_weather_forecast AS f
INNER JOIN mart.latest_pipeline_run AS r
    ON f.run_id = r.run_id;

CREATE OR REPLACE VIEW mart.latest_daily_weather_summary AS
SELECT d.*
FROM mart.daily_weather_summary AS d
INNER JOIN mart.latest_pipeline_run AS r
    ON d.run_id = r.run_id;
