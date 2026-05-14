-- Müük tootekategooria ja kuu lõikes
select
    d.month_start,
    d.year,
    d.month,
    p.category,
    p.brand,
    count(distinct f.sale_id)       as tehinguid,
    sum(f.quantity)                 as kogus_kokku,
    sum(f.sales_amount)             as tulu_kokku
from "praktikum"."staging"."stg_fact_sales"   f
join "praktikum"."staging"."stg_dim_date"     d on f.date_key    = d.date_key
join "praktikum"."staging"."stg_dim_product"  p on f.product_key = p.product_key
group by d.month_start, d.year, d.month, p.category, p.brand
order by d.month_start, p.category