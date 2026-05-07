-- Muuk piirkonna ja kuu loikes
select
    d.month_start,
    d.year,
    d.month,
    s.region,
    s.city,
    s.store_name,
    count(distinct f.sale_id)       as tehinguid,
    sum(f.quantity)                 as kogus_kokku,
    sum(f.sales_amount)             as tulu_kokku
from {{ ref('stg_fact_sales') }}  f
join {{ ref('stg_dim_date') }}    d on f.date_key  = d.date_key
join {{ ref('stg_dim_store') }}   s on f.store_key = s.store_key
group by d.month_start, d.year, d.month, s.region, s.city, s.store_name
order by d.month_start, s.region
