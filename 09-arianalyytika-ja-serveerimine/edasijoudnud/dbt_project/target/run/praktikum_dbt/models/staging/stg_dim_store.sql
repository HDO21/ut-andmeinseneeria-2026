
  create view "praktikum"."staging"."stg_dim_store__dbt_tmp"
    
    
  as (
    select
    store_key,
    store_name,
    city,
    region
from "praktikum"."raw"."dim_store"
  );