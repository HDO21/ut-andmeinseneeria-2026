-- 9. praktikumi andmebaasi objektid.
--
-- Superset kasutab sama PostgreSQL serverit oma metaandmete jaoks `public`
-- skeemis. Praktikumi andmed hoiame eraldi skeemides, et õppeandmed ja
-- tööriista sisetabelid ei läheks segamini.

-- Praktikumi äripäev on Tallinna aja järgi. TIMESTAMPTZ hoiab ajahetke koos
-- ajavööndi infoga, aga päevaks lõikamisel ütleme ajavööndi alati selgelt.
SET TIME ZONE 'Europe/Tallinn';

-- `staging` on maandumiskiht. Siia jõuavad andmed võimalikult allikalähedasel
-- kujul.
CREATE SCHEMA IF NOT EXISTS staging;

-- `intermediate` on vahekiht, kus sündmused seotakse kirjeldavate tunnustega.
CREATE SCHEMA IF NOT EXISTS intermediate;

-- `analytics` sisaldab Supersetile mõeldud analüütilisi vaateid.
CREATE SCHEMA IF NOT EXISTS analytics;

-- `monitoring` sisaldab töövoo logi, mida näitame samuti Supersetis.
CREATE SCHEMA IF NOT EXISTS monitoring;

-- `control` hoiab töövoo järjehoidjat ehk infot, kust järgmine mikrobatch jätkab.
CREATE SCHEMA IF NOT EXISTS control;

-- Toodete ja poodide tabelid on dimensiooniandmed.
-- Need kirjeldavad, mida ja kus müüdi.
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

-- Müügisündmuste tabel on faktitabeli algne kiht.
-- Iga rida tähendab ühte sünteetilist tellimust.
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

-- Indeksid aitavad Supersetil ajas ja toote/poe lõikes kiiremini pärida.
CREATE INDEX IF NOT EXISTS idx_order_events_event_time
    ON staging.order_events (event_time);

CREATE INDEX IF NOT EXISTS idx_order_events_store_product
    ON staging.order_events (store_id, product_id);

-- Iga mikrobatch kirjutab siia ühe rea.
-- Dashboardi logitabel loeb andmeid sellest tabelist.
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

-- Töövoo järjehoidja. Kui cron järgmine kord käivitub, loeb ta siit, millise
-- event_sequence väärtusega jätkata.
CREATE TABLE IF NOT EXISTS control.pipeline_state (
    state_key TEXT PRIMARY KEY,
    next_event_sequence BIGINT NOT NULL,
    next_event_time TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Rikastatud sündmuste vaade seob tellimuse toote ja poe andmetega.
CREATE OR REPLACE VIEW intermediate.v_sales_events_enriched AS
SELECT
    e.event_id,
    e.event_sequence,
    e.order_id,
    e.event_time,
    (e.event_time AT TIME ZONE 'Europe/Tallinn')::date AS sales_date,
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

-- See vaade on Supersetis olemas juhul, kui õppija tahab uurida üksiksündmusi.
CREATE OR REPLACE VIEW analytics.v_sales_events AS
SELECT *
FROM intermediate.v_sales_events_enriched;

-- Päeva, poe, piirkonna ja kategooria koond. Seda kasutatakse trendijoonisel.
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

-- Kategooriate koond. Seda kasutatakse tulpdiagrammi jaoks.
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

-- Piirkondade koond valikulise lisaharjutuse jaoks.
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

-- Päevatasemeline KPI vaade starter-dashboardi jaoks.
-- See sisaldab `sales_date` veergu, et Superseti ajafilter saaks KPI-d ja
-- teisi müügijooniseid sama kuupäeva alusel filtreerida.
CREATE OR REPLACE VIEW analytics.v_dashboard_kpi AS
SELECT
    sales_date,
    COUNT(DISTINCT order_id)::INTEGER AS total_orders,
    COALESCE(SUM(quantity), 0)::INTEGER AS total_quantity,
    COALESCE(ROUND(SUM(total_amount_eur), 2), 0)::NUMERIC(14, 2) AS total_revenue_eur,
    COALESCE(ROUND(AVG(total_amount_eur), 2), 0)::NUMERIC(12, 2) AS avg_order_eur,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time,
    MAX(processed_at) AS last_processed_at
FROM analytics.v_sales_events
GROUP BY sales_date;

-- Viimased töövoo käivitused. Supersetis on sellest starter-dashboardi tabel.
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
