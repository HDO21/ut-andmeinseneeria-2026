
  create view "praktikum"."staging"."stg_dim_product__dbt_tmp"
    
    
  as (
    select
    product_key,
    product_name,
    category,
    brand
from "praktikum"."raw"."dim_product"
  );