SELECT COUNT(*) AS products_rows
FROM staging.products_raw;

SELECT COUNT(*) AS stores_rows
FROM staging.stores_raw;

SELECT COUNT(*) AS order_events_rows
FROM staging.order_events;

SELECT
    sales_date,
    SUM(order_count) AS order_count,
    SUM(gross_sales_eur) AS gross_sales_eur
FROM analytics.v_sales_daily
GROUP BY sales_date
ORDER BY sales_date;

SELECT
    run_type,
    status,
    rows_inserted,
    watermark_from,
    watermark_to,
    message,
    finished_at
FROM monitoring.v_recent_microbatch_runs
ORDER BY id DESC
LIMIT 10;
