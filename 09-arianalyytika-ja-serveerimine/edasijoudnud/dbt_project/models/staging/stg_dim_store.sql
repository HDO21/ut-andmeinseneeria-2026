select
    store_key,
    store_name,
    city,
    region
from {{ source('raw', 'dim_store') }}
