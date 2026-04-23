-- Turunduse vaade kasutajatele: PII veerud (nimi, email) on vaatest täielikult väljas
-- marketing-roll ei näe veerge first_name, last_name, full_name, email
-- SELECT email FROM secured.dim_users_marketing -> ERROR: column "email" does not exist
-- Stsenaarium A: veerg puudub vaatest

{{ config(
    materialized='view',
    schema='secured',
    grants={'select': ['marketing']}
) }}

SELECT
    {{ masked_columns('dim_users', role='marketing') }}
FROM {{ ref('dim_users') }}
