select
    customer_key,
    customer_id,
    first_name || ' ' || last_name as full_name,
    segment,
    city,
    valid_from,
    valid_to,
    valid_to = '9999-12-31'::date as is_current
from {{ source('raw', 'dim_customer') }}
