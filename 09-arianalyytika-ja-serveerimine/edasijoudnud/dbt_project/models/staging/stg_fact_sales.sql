select
    sale_id,
    date_key,
    store_key,
    product_key,
    supplier_key,
    customer_key,
    payment_key,
    quantity,
    sales_amount,
    full_date
from {{ source('raw', 'fact_sales') }}
