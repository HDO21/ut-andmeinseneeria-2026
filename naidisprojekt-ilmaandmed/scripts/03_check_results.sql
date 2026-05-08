SELECT
    run_id,
    fetched_at,
    source_name,
    forecast_days,
    status
FROM staging.pipeline_runs
ORDER BY fetched_at DESC
LIMIT 5;

SELECT
    location_name,
    forecast_date,
    avg_temp_c,
    total_precipitation_mm,
    max_wind_speed_ms,
    weather_risk_level
FROM mart.latest_daily_weather_summary
ORDER BY location_name, forecast_date
LIMIT 20;

SELECT
    test_name,
    status,
    failed_rows,
    message
FROM quality.test_results
ORDER BY test_name;
