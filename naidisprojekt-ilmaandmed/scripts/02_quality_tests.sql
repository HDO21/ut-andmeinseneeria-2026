TRUNCATE TABLE quality.test_results;

WITH latest_run AS (
    SELECT run_id
    FROM staging.pipeline_runs
    WHERE status = 'success'
    ORDER BY fetched_at DESC
    LIMIT 1
),
test_cases AS (
    SELECT
        'weather_raw_has_rows' AS test_name,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM staging.weather_hourly_raw AS w
                INNER JOIN latest_run AS r ON w.run_id = r.run_id
            )
                THEN 0
            ELSE 1
        END AS failed_rows,
        'Viimasel edukal laadimisel peab olema vähemalt üks ilmarida.' AS message

    UNION ALL

    SELECT
        'latest_run_has_expected_locations' AS test_name,
        GREATEST(2 - COUNT(DISTINCT w.location_id), 0)::integer AS failed_rows,
        'Viimasel edukal laadimisel peavad olema nii Tartu kui Tallinn.' AS message
    FROM latest_run AS r
    LEFT JOIN staging.weather_hourly_raw AS w
        ON r.run_id = w.run_id

    UNION ALL

    SELECT
        'forecast_time_not_null' AS test_name,
        COUNT(*)::integer AS failed_rows,
        'Prognoosi aeg ei tohi puududa.' AS message
    FROM staging.weather_hourly_raw AS w
    INNER JOIN latest_run AS r ON w.run_id = r.run_id
    WHERE w.forecast_time IS NULL

    UNION ALL

    SELECT
        'unique_location_time_per_run' AS test_name,
        COUNT(*)::integer AS failed_rows,
        'Sama käivituse, asukoha ja tunni kohta tohib olla üks rida.' AS message
    FROM (
        SELECT
            w.run_id,
            w.location_id,
            w.forecast_time,
            COUNT(*) AS row_count
        FROM staging.weather_hourly_raw AS w
        INNER JOIN latest_run AS r ON w.run_id = r.run_id
        GROUP BY
            w.run_id,
            w.location_id,
            w.forecast_time
        HAVING COUNT(*) > 1
    ) AS duplicates

    UNION ALL

    SELECT
        'temperature_reasonable' AS test_name,
        COUNT(*)::integer AS failed_rows,
        'Temperatuur peab jääma vahemikku -50 kuni 50 kraadi.' AS message
    FROM staging.weather_hourly_raw AS w
    INNER JOIN latest_run AS r ON w.run_id = r.run_id
    WHERE w.temperature_c IS NULL
       OR w.temperature_c < -50
       OR w.temperature_c > 50

    UNION ALL

    SELECT
        'precipitation_not_negative' AS test_name,
        COUNT(*)::integer AS failed_rows,
        'Sademed ei tohi olla negatiivsed.' AS message
    FROM staging.weather_hourly_raw AS w
    INNER JOIN latest_run AS r ON w.run_id = r.run_id
    WHERE w.precipitation_mm IS NULL
       OR w.precipitation_mm < 0

    UNION ALL

    SELECT
        'wind_speed_reasonable' AS test_name,
        COUNT(*)::integer AS failed_rows,
        'Tuulekiirus peab jääma vahemikku 0 kuni 60 m/s.' AS message
    FROM staging.weather_hourly_raw AS w
    INNER JOIN latest_run AS r ON w.run_id = r.run_id
    WHERE w.wind_speed_ms IS NULL
       OR w.wind_speed_ms < 0
       OR w.wind_speed_ms > 60

    UNION ALL

    SELECT
        'mart_daily_summary_has_rows' AS test_name,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM mart.latest_daily_weather_summary
            )
                THEN 0
            ELSE 1
        END AS failed_rows,
        'Päevane koondtabel peab sisaldama näidikulaua ridu.' AS message
)
INSERT INTO quality.test_results (
    test_name,
    status,
    failed_rows,
    message
)
SELECT
    test_name,
    CASE WHEN failed_rows = 0 THEN 'passed' ELSE 'failed' END AS status,
    failed_rows,
    message
FROM test_cases
ORDER BY test_name;
