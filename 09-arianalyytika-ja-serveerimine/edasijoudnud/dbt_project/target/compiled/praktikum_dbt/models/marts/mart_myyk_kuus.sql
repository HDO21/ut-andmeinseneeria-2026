-- Igakuine müük: kogutulu, tehingute arv, keskmine ostu suurus
select
    d.month_start,
    d.year,
    d.month,
    count(distinct f.sale_id)       as tehinguid,
    sum(f.quantity)                 as kogus_kokku,
    sum(f.sales_amount)             as tulu_kokku,
    round(avg(f.sales_amount), 2)   as keskmine_ostu_suurus
from "praktikum"."staging"."stg_fact_sales" f
join "praktikum"."staging"."stg_dim_date"    d on f.date_key = d.date_key
group by d.month_start, d.year, d.month
order by d.month_start