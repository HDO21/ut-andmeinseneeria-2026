-- Kiire kontroll pärast `docker compose up -d --build` käivitamist.
-- Käivita see juhendis antud `docker compose exec scheduler psql ...` käsuga.

-- Kas andmebaasi sessioon kasutab praktikumi kohalikku ajavööndit?
SHOW timezone;

-- Kas tootekataloog jõudis andmebaasi?
SELECT COUNT(*) AS products_rows
FROM staging.products_raw;

-- Kas poodide kataloog jõudis andmebaasi?
SELECT COUNT(*) AS stores_rows
FROM staging.stores_raw;

-- Kas alglaadimine või cron on müügisündmusi lisanud?
SELECT COUNT(*) AS order_events_rows
FROM staging.order_events;

-- Kui palju tellimusi ja käivet on päevade kaupa?
SELECT
    sales_date,
    SUM(order_count) AS order_count,
    SUM(gross_sales_eur) AS gross_sales_eur
FROM analytics.v_sales_daily
GROUP BY sales_date
ORDER BY sales_date;

-- Millised olid viimased mikrobatch töövoo käivitused?
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
