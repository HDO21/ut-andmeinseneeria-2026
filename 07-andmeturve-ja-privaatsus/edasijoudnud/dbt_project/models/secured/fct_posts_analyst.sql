-- Analüütiku vaade postitustele: autori nimi maskeeritud
-- analyst-roll näeb postitusi koos maskeeritud autori nimega

{{ config(
    materialized='view',
    schema='secured',
    grants={'select': ['analyst']}
) }}

SELECT
    {{ masked_columns('fct_posts', role='analyst') }}
FROM {{ ref('fct_posts') }}
