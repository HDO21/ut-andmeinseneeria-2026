"""
Andmete laadimine CSV-failidest PostgreSQL raw-skeemasse (01_load_data.py)

Loeb /data kaustast supermarketi CSV-failid ja laeb need andmebaasi raw-skeemasse.

Kasutamine:
  python 01_load_data.py                      # laadi kõik tabelid
  python 01_load_data.py --tabel fact_sales   # laadi üks tabel
"""

import argparse
import logging
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = "/data"


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "praktikum"),
        password=os.environ.get("DB_PASSWORD", "praktikum"),
        dbname=os.environ.get("DB_NAME", "praktikum"),
    )


DDL = {
    "dim_date": """
        CREATE TABLE IF NOT EXISTS raw.dim_date (
            date_key    INTEGER PRIMARY KEY,
            full_date   DATE,
            year        SMALLINT,
            month       SMALLINT,
            day         SMALLINT,
            day_of_week TEXT
        )
    """,
    "dim_store": """
        CREATE TABLE IF NOT EXISTS raw.dim_store (
            store_key   INTEGER PRIMARY KEY,
            store_name  TEXT,
            city        TEXT,
            region      TEXT
        )
    """,
    "dim_product": """
        CREATE TABLE IF NOT EXISTS raw.dim_product (
            product_key   INTEGER PRIMARY KEY,
            product_name  TEXT,
            category      TEXT,
            brand         TEXT
        )
    """,
    "dim_supplier": """
        CREATE TABLE IF NOT EXISTS raw.dim_supplier (
            supplier_key   INTEGER PRIMARY KEY,
            supplier_name  TEXT,
            contact_info   TEXT
        )
    """,
    "dim_customer": """
        CREATE TABLE IF NOT EXISTS raw.dim_customer (
            customer_key  INTEGER PRIMARY KEY,
            customer_id   INTEGER,
            first_name    TEXT,
            last_name     TEXT,
            segment       TEXT,
            city          TEXT,
            valid_from    DATE,
            valid_to      DATE
        )
    """,
    "dim_payment": """
        CREATE TABLE IF NOT EXISTS raw.dim_payment (
            payment_key   INTEGER PRIMARY KEY,
            payment_type  TEXT
        )
    """,
    "fact_sales": """
        CREATE TABLE IF NOT EXISTS raw.fact_sales (
            sale_id       BIGINT PRIMARY KEY,
            date_key      INTEGER,
            store_key     INTEGER,
            product_key   INTEGER,
            supplier_key  INTEGER,
            customer_key  INTEGER,
            payment_key   INTEGER,
            quantity      SMALLINT,
            sales_amount  NUMERIC(10,2),
            full_date     DATE
        )
    """,
}

CSV_COLUMNS = {
    "dim_date":     ["DateKey", "FullDate", "Year", "Month", "Day", "DayOfWeek"],
    "dim_store":    ["StoreKey", "StoreName", "City", "Region"],
    "dim_product":  ["ProductKey", "ProductName", "Category", "Brand"],
    "dim_supplier": ["SupplierKey", "SupplierName", "ContactInfo"],
    "dim_customer": ["CustomerKey", "CustomerID", "FirstName", "LastName", "Segment", "City", "ValidFrom", "ValidTo"],
    "dim_payment":  ["PaymentKey", "PaymentType"],
    "fact_sales":   ["SaleID", "DateKey", "StoreKey", "ProductKey", "SupplierKey", "CustomerKey", "PaymentKey", "Quantity", "SalesAmount", "FullDate"],
}

LOAD_ORDER = ["dim_date", "dim_store", "dim_product", "dim_supplier", "dim_customer", "dim_payment", "fact_sales"]


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        for ddl in DDL.values():
            cur.execute(ddl)
    conn.commit()
    logger.info("Raw skeema ja tabelid valmis.")


def load_table(conn, tabel: str):
    csv_path = os.path.join(DATA_DIR, f"{tabel}.csv")
    if not os.path.exists(csv_path):
        logger.warning("Fail puudub, jatan vahele: %s", csv_path)
        return

    df = pd.read_csv(csv_path, usecols=CSV_COLUMNS[tabel])
    df.columns = [c.lower() for c in df.columns]

    # Normaliseeri veergude nimed csv -> db
    rename = {
        "datekey": "date_key", "fulldate": "full_date", "dayofweek": "day_of_week",
        "storekey": "store_key", "storename": "store_name",
        "productkey": "product_key", "productname": "product_name",
        "supplierkey": "supplier_key", "suppliername": "supplier_name", "contactinfo": "contact_info",
        "customerkey": "customer_key", "customerid": "customer_id",
        "firstname": "first_name", "lastname": "last_name",
        "validfrom": "valid_from", "validto": "valid_to",
        "paymentkey": "payment_key", "paymenttype": "payment_type",
        "saleid": "sale_id", "salesamount": "sales_amount",
    }
    df.rename(columns=rename, inplace=True)

    cols = list(df.columns)
    rows = [tuple(r) for r in df.itertuples(index=False, name=None)]
    col_str = ", ".join(cols)
    placeholders = "(" + ", ".join(["%s"] * len(cols)) + ")"

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE raw.{tabel};")
        execute_values(cur, f"INSERT INTO raw.{tabel} ({col_str}) VALUES %s", rows)
    conn.commit()
    logger.info("%-15s -> %d rida laaditud.", tabel, len(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tabel", choices=list(DDL.keys()), default=None,
                        help="Laadi ainult uks tabel (vaikimisi koik)")
    args = parser.parse_args()

    conn = get_connection()
    try:
        ensure_schema(conn)
        tabelid = [args.tabel] if args.tabel else LOAD_ORDER
        for t in tabelid:
            load_table(conn, t)
    finally:
        conn.close()

    logger.info("Valmis.")


if __name__ == "__main__":
    main()
