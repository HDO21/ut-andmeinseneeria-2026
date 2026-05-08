CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS quality;

CREATE TABLE IF NOT EXISTS staging.pipeline_runs (
    run_id uuid PRIMARY KEY,
    fetched_at timestamptz NOT NULL,
    source_name text NOT NULL,
    forecast_days integer NOT NULL,
    status text NOT NULL,
    message text
);

CREATE TABLE IF NOT EXISTS staging.weather_hourly_raw (
    run_id uuid NOT NULL REFERENCES staging.pipeline_runs (run_id),
    location_id text NOT NULL,
    location_name text NOT NULL,
    latitude numeric(9, 4) NOT NULL,
    longitude numeric(9, 4) NOT NULL,
    forecast_time timestamp NOT NULL,
    temperature_c numeric(6, 2),
    precipitation_mm numeric(8, 2),
    wind_speed_ms numeric(8, 2),
    fetched_at timestamptz NOT NULL,
    source_url text NOT NULL,
    PRIMARY KEY (run_id, location_id, forecast_time)
);

CREATE TABLE IF NOT EXISTS mart.dim_location (
    location_id text PRIMARY KEY,
    location_name text NOT NULL,
    country text NOT NULL,
    latitude numeric(9, 4) NOT NULL,
    longitude numeric(9, 4) NOT NULL
);

CREATE TABLE IF NOT EXISTS mart.fact_weather_forecast (
    run_id uuid NOT NULL,
    location_id text NOT NULL REFERENCES mart.dim_location (location_id),
    forecast_time timestamp NOT NULL,
    forecast_date date NOT NULL,
    temperature_c numeric(6, 2),
    precipitation_mm numeric(8, 2),
    wind_speed_ms numeric(8, 2),
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (run_id, location_id, forecast_time)
);

CREATE TABLE IF NOT EXISTS mart.daily_weather_summary (
    run_id uuid NOT NULL,
    location_id text NOT NULL REFERENCES mart.dim_location (location_id),
    location_name text NOT NULL,
    forecast_date date NOT NULL,
    forecast_hours integer NOT NULL,
    avg_temp_c numeric(6, 2),
    max_temp_c numeric(6, 2),
    total_precipitation_mm numeric(8, 2),
    max_wind_speed_ms numeric(8, 2),
    hours_with_precipitation integer NOT NULL,
    weather_risk_level text NOT NULL,
    PRIMARY KEY (run_id, location_id, forecast_date)
);

CREATE TABLE IF NOT EXISTS quality.test_results (
    test_run_at timestamptz NOT NULL DEFAULT now(),
    test_name text NOT NULL,
    status text NOT NULL,
    failed_rows integer NOT NULL,
    message text NOT NULL
);

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
