CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS control;

CREATE TABLE IF NOT EXISTS staging.products_raw (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    base_price_eur NUMERIC(10, 2) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.stores_raw (
    store_id TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    city TEXT NOT NULL,
    region TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.order_events (
    event_id TEXT PRIMARY KEY,
    event_sequence BIGINT UNIQUE NOT NULL,
    order_id TEXT UNIQUE NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    store_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_eur NUMERIC(10, 2) NOT NULL CHECK (unit_price_eur >= 0),
    source_batch_id UUID NOT NULL,
    is_backfill BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_order_events_event_time
    ON staging.order_events (event_time);

CREATE INDEX IF NOT EXISTS idx_order_events_store_product
    ON staging.order_events (store_id, product_id);

CREATE TABLE IF NOT EXISTS monitoring.microbatch_run_log (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    run_type TEXT NOT NULL,
    status TEXT NOT NULL,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    watermark_from TIMESTAMPTZ,
    watermark_to TIMESTAMPTZ,
    message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT microbatch_status_check
        CHECK (status IN ('success', 'error', 'skipped'))
);

CREATE TABLE IF NOT EXISTS control.pipeline_state (
    state_key TEXT PRIMARY KEY,
    next_event_sequence BIGINT NOT NULL,
    next_event_time TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW analytics.v_sales_events AS
SELECT
    e.event_id,
    e.event_sequence,
    e.order_id,
    e.event_time,
    e.event_time::date AS sales_date,
    e.processed_at,
    e.store_id,
    s.store_name,
    s.city,
    s.region,
    e.product_id,
    p.product_name,
    p.category,
    e.quantity,
    e.unit_price_eur,
    ROUND(e.quantity * e.unit_price_eur, 2)::NUMERIC(12, 2) AS total_amount_eur,
    e.source_batch_id,
    e.is_backfill
FROM staging.order_events AS e
LEFT JOIN staging.stores_raw AS s
    ON e.store_id = s.store_id
LEFT JOIN staging.products_raw AS p
    ON e.product_id = p.product_id;

CREATE OR REPLACE VIEW analytics.v_sales_daily AS
SELECT
    sales_date,
    store_id,
    store_name,
    region,
    category,
    COUNT(DISTINCT order_id)::INTEGER AS order_count,
    SUM(quantity)::INTEGER AS total_quantity,
    ROUND(SUM(total_amount_eur), 2)::NUMERIC(14, 2) AS gross_sales_eur,
    ROUND(AVG(total_amount_eur), 2)::NUMERIC(12, 2) AS avg_order_eur,
    MAX(processed_at) AS last_processed_at
FROM analytics.v_sales_events
GROUP BY
    sales_date,
    store_id,
    store_name,
    region,
    category;

CREATE OR REPLACE VIEW analytics.v_sales_by_category AS
SELECT
    sales_date,
    category,
    COUNT(DISTINCT order_id)::INTEGER AS order_count,
    SUM(quantity)::INTEGER AS total_quantity,
    ROUND(SUM(total_amount_eur), 2)::NUMERIC(14, 2) AS gross_sales_eur,
    ROUND(AVG(total_amount_eur), 2)::NUMERIC(12, 2) AS avg_order_eur,
    MAX(processed_at) AS last_processed_at
FROM analytics.v_sales_events
GROUP BY
    sales_date,
    category;

CREATE OR REPLACE VIEW analytics.v_sales_by_region AS
SELECT
    sales_date,
    region,
    COUNT(DISTINCT order_id)::INTEGER AS order_count,
    SUM(quantity)::INTEGER AS total_quantity,
    ROUND(SUM(total_amount_eur), 2)::NUMERIC(14, 2) AS gross_sales_eur,
    ROUND(AVG(total_amount_eur), 2)::NUMERIC(12, 2) AS avg_order_eur,
    MAX(processed_at) AS last_processed_at
FROM analytics.v_sales_events
GROUP BY
    sales_date,
    region;

CREATE OR REPLACE VIEW analytics.v_dashboard_kpi AS
SELECT
    1::INTEGER AS row_id,
    COUNT(DISTINCT order_id)::INTEGER AS total_orders,
    COALESCE(SUM(quantity), 0)::INTEGER AS total_quantity,
    COALESCE(ROUND(SUM(total_amount_eur), 2), 0)::NUMERIC(14, 2) AS total_revenue_eur,
    COALESCE(ROUND(AVG(total_amount_eur), 2), 0)::NUMERIC(12, 2) AS avg_order_eur,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time,
    MAX(processed_at) AS last_processed_at
FROM analytics.v_sales_events;

CREATE OR REPLACE VIEW monitoring.v_recent_microbatch_runs AS
SELECT
    id,
    run_type,
    status,
    rows_inserted,
    watermark_from,
    watermark_to,
    message,
    started_at,
    finished_at
FROM monitoring.microbatch_run_log
ORDER BY id DESC
LIMIT 20;
