select
    product_key,
    product_name,
    category,
    brand
from {{ source('raw', 'dim_product') }}
