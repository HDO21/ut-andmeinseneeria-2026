-- Analüütiku vaade kasutajatele: PII on maskeeritud, kõik veerud nähtavad
-- analyst-roll näeb maskeeritud emaili, linna ja nimesid
-- Registreerumiskuupäev trunkeeritud kuu täpsusega

{{ config(
    materialized='view',
    schema='secured',
    grants={'select': ['analyst']}
) }}

SELECT
    {{ masked_columns('dim_users', role='analyst') }}
FROM {{ ref('dim_users') }}
