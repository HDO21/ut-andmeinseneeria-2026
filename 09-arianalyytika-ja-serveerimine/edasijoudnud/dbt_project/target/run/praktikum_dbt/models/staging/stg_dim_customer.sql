
  create view "praktikum"."staging"."stg_dim_customer__dbt_tmp"
    
    
  as (
    select
    customer_key,
    customer_id,
    first_name || ' ' || last_name as full_name,
    segment,
    city,
    valid_from,
    valid_to,
    valid_to = '9999-12-31'::date as is_current
from "praktikum"."raw"."dim_customer"
  );