
  create view "praktikum"."staging"."stg_dim_date__dbt_tmp"
    
    
  as (
    select
    date_key,
    full_date,
    year,
    month,
    day,
    day_of_week,
    date_trunc('month', full_date)::date as month_start,
    date_trunc('quarter', full_date)::date as quarter_start
from "praktikum"."raw"."dim_date"
  );