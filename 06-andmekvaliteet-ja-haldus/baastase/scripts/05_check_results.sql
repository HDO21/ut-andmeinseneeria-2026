-- See fail koondab praktikumi peamised kontrollpäringud ühte kohta.
-- Mõte on lihtne:
-- üks käsk, mitu vaadet tulemusele.

SELECT
    COUNT(*) AS product_snapshot_rows
FROM staging.product_snapshots_raw;

SELECT
    COUNT(*) AS store_snapshot_rows
FROM staging.store_snapshots_raw;

SELECT
    order_date,
    COUNT(*) AS order_rows
FROM staging.orders_raw
GROUP BY order_date
ORDER BY order_date;

SELECT
    product_id,
    product_name,
    base_price_eur,
    valid_from,
    valid_to,
    is_current
FROM intermediate.dim_products_scd
ORDER BY product_id, valid_from;

SELECT
    rule_name,
    failed_rows
FROM quality.order_issue_summary
ORDER BY failed_rows DESC, rule_name;

SELECT
    o.order_date,
    o.order_id,
    o.store_id,
    o.product_id,
    o.quantity,
    o.unit_price_eur,
    STRING_AGG(r.rule_name, ', ' ORDER BY r.rule_name) AS failed_rules
FROM staging.orders_raw AS o
INNER JOIN quality.order_rule_results AS r
    ON o.staging_row_id = r.staging_row_id
GROUP BY
    o.order_date,
    o.order_id,
    o.store_id,
    o.product_id,
    o.quantity,
    o.unit_price_eur
ORDER BY o.order_date, o.order_id NULLS LAST;

SELECT
    raw_order_rows,
    clean_order_rows,
    rejected_row_count,
    total_rule_failures,
    rejected_row_percent
FROM analytics.quality_overview;

SELECT
    sales_date,
    store_name,
    product_name,
    total_quantity,
    gross_sales_eur
FROM analytics.daily_product_sales_clean
ORDER BY sales_date, store_name, product_name;

SELECT
    asset_name,
    owner_name,
    refresh_frequency,
    source_system
FROM governance.data_asset_registry
ORDER BY asset_name;

SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    obj_description(c.oid, 'pg_class') AS table_comment
FROM pg_class AS c
INNER JOIN pg_namespace AS n
    ON n.oid = c.relnamespace
WHERE n.nspname IN ('intermediate', 'quality', 'analytics', 'governance')
  AND c.relname IN (
      'dim_products_scd',
      'dim_stores_scd',
      'order_rule_results',
      'orders_clean',
      'daily_product_sales_clean',
      'data_asset_registry'
  )
ORDER BY n.nspname, c.relname;
