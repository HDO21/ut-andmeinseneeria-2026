-- Ehita kuistest snapshotitest aeglikud dimensioonid.
--
-- Iga toote ja poe kohta võib olla mitu versiooni.
-- Kehtivusvahemik aitab hiljem siduda tellimuse just selle kirjeldusega,
-- mis oli tellimuse kuupäeval päriselt kehtiv.

DROP TABLE IF EXISTS intermediate.dim_products_scd;
DROP TABLE IF EXISTS intermediate.dim_stores_scd;

CREATE TABLE intermediate.dim_products_scd AS
WITH ordered_snapshots AS (
    SELECT
        product_id,
        TRIM(product_name) AS product_name,
        TRIM(category) AS category,
        base_price_eur,
        snapshot_month AS valid_from,
        LEAD(snapshot_month) OVER (
            PARTITION BY product_id
            ORDER BY snapshot_month
        ) AS next_valid_from
    FROM staging.product_snapshots_raw
)
SELECT
    product_id || ':' || TO_CHAR(valid_from, 'YYYY-MM-DD') AS product_version_key,
    product_id,
    product_name,
    category,
    base_price_eur,
    valid_from,
    COALESCE(next_valid_from - 1, DATE '9999-12-31') AS valid_to,
    next_valid_from IS NULL AS is_current
FROM ordered_snapshots;

ALTER TABLE intermediate.dim_products_scd
    ADD PRIMARY KEY (product_version_key);

CREATE INDEX idx_dim_products_scd_lookup
    ON intermediate.dim_products_scd (product_id, valid_from, valid_to);

CREATE TABLE intermediate.dim_stores_scd AS
WITH ordered_snapshots AS (
    SELECT
        store_id,
        TRIM(store_name) AS store_name,
        TRIM(city) AS city,
        TRIM(region) AS region,
        snapshot_month AS valid_from,
        LEAD(snapshot_month) OVER (
            PARTITION BY store_id
            ORDER BY snapshot_month
        ) AS next_valid_from
    FROM staging.store_snapshots_raw
)
SELECT
    store_id || ':' || TO_CHAR(valid_from, 'YYYY-MM-DD') AS store_version_key,
    store_id,
    store_name,
    city,
    region,
    valid_from,
    COALESCE(next_valid_from - 1, DATE '9999-12-31') AS valid_to,
    next_valid_from IS NULL AS is_current
FROM ordered_snapshots;

ALTER TABLE intermediate.dim_stores_scd
    ADD PRIMARY KEY (store_version_key);

CREATE INDEX idx_dim_stores_scd_lookup
    ON intermediate.dim_stores_scd (store_id, valid_from, valid_to);
