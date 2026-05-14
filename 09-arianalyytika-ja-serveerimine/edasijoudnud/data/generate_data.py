"""
Genereerib supermarketi müügiandmed 2025-01-01 kuni 2026-04-30.
Käivita: python generate_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent

START = date(2025, 1, 1)
END   = date(2026, 4, 30)

# --- Dimensioonid (hoiame sama struktuuri) ---

STORES = [
    (1, "SuperMart Downtown", "Tallinn", "North"),
    (2, "SuperMart Suburb",   "Tartu",   "South"),
]

PRODUCTS = [
    (1, "Apple",  "Fruit",   "FreshFarm"),
    (2, "Banana", "Fruit",   "Tropicana"),
    (3, "Milk",   "Dairy",   "DairyBest"),
    (4, "Bread",  "Bakery",  "BakeHouse"),
]

UNIT_PRICES = {1: 1.20, 2: 0.80, 3: 2.50, 4: 1.50}

SUPPLIERS = [
    (1, "FreshFarm Supplier",  "fresh@farm.com"),
    (2, "Tropicana Supplier",  "contact@tropicana.com"),
    (3, "DairyBest Supplier",  "sales@dairybest.com"),
    (4, "BakeHouse Supplier",  "info@bakehouse.com"),
]

PAYMENTS = [(1, "Cash"), (2, "Card"), (3, "Voucher")]

FIRST_NAMES = ["Alice","Bob","Carol","David","Eve","Frank","Grace","Henry",
               "Iris","Jack","Karen","Leo","Maria","Nick","Olivia","Peter",
               "Quinn","Rachel","Sam","Tina","Urmas","Valve","Marek","Liisi"]
LAST_NAMES  = ["Smith","Jones","Brown","Wilson","Taylor","Davis","Miller",
               "Moore","Anderson","Thomas","Tamm","Mägi","Kask","Rebane"]
SEGMENTS    = ["Regular","VIP","Premium"]
CITIES      = ["Tallinn","Tartu","Narva","Pärnu","Viljandi"]

CUSTOMERS = []
for i in range(1, 41):
    CUSTOMERS.append((
        i, i,
        FIRST_NAMES[(i - 1) % len(FIRST_NAMES)],
        LAST_NAMES[(i - 1)  % len(LAST_NAMES)],
        SEGMENTS[i % 3],
        CITIES[i % len(CITIES)],
        "2025-01-01", "9999-12-31",
    ))

# --- Hooajalisus ja mustrid ---

MONTH_MULT = {
    1: 0.80, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.10,
    7: 1.15, 8: 1.10, 9: 1.05, 10: 1.00, 11: 1.15, 12: 1.45,
}

# Toote eelistus kuu kaupa (kaalud random.choices jaoks)
PRODUCT_MONTH_WEIGHT = {
    1: [0.8,0.8,0.9,1.0,1.2,1.5,1.6,1.5,1.2,1.0,0.9,1.0],  # Apple
    2: [0.7,0.7,0.8,1.0,1.2,1.5,1.7,1.5,1.1,0.9,0.8,0.9],  # Banana
    3: [1.2,1.2,1.1,1.0,0.9,0.8,0.8,0.8,1.0,1.1,1.2,1.3],  # Milk
    4: [1.1,1.1,1.0,1.0,0.9,0.9,0.9,0.9,1.0,1.0,1.1,1.4],  # Bread
}

# Tallinn suurem pood (~60% tehingutest)
STORE_BASE = {1: 18, 2: 12}

# --- Genereeri dim_date ---

all_dates = []
date_key_map = {}
dk = 1
d = START
while d <= END:
    all_dates.append((dk, d.isoformat(), d.year, d.month, d.day, d.strftime("%A")))
    date_key_map[d.isoformat()] = dk
    dk += 1
    d += timedelta(days=1)

# --- Genereeri fact_sales ---

fact_sales = []
sale_id = 1

d = START
while d <= END:
    date_str = d.isoformat()
    dk = date_key_map[date_str]
    is_weekend   = d.weekday() >= 5
    weekend_mult = 1.35 if is_weekend else 1.0
    month_mult   = MONTH_MULT[d.month]
    month_idx    = d.month - 1  # 0-based for list index

    for store_key, _, city, region in STORES:
        base = STORE_BASE[store_key]
        n = max(3, int(base * month_mult * weekend_mult * random.uniform(0.75, 1.25)))

        for _ in range(n):
            weights     = [PRODUCT_MONTH_WEIGHT[pk][month_idx] for pk in [1, 2, 3, 4]]
            product_key = random.choices([1, 2, 3, 4], weights=weights)[0]
            supplier_key = product_key  # 1:1 seos

            qty = random.randint(1, 8) if product_key in (1, 2) else random.randint(1, 4)
            price  = UNIT_PRICES[product_key]
            amount = round(qty * price * random.uniform(0.95, 1.05), 2)

            customer_key = random.randint(1, len(CUSTOMERS))
            payment_key  = random.choices([1, 2, 3], weights=[25, 65, 10])[0]

            fact_sales.append((
                sale_id, dk, store_key, product_key, supplier_key,
                customer_key, payment_key, qty, amount, date_str,
            ))
            sale_id += 1

    d += timedelta(days=1)

# --- Kirjuta CSV-failid ---

def write_csv(fname, header, rows):
    path = DATA_DIR / fname
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {fname}: {len(rows)} rida")

print("Kirjutan CSV-failid...")
write_csv("dim_date.csv",
          ["DateKey","FullDate","Year","Month","Day","DayOfWeek"],
          all_dates)

write_csv("dim_store.csv",
          ["StoreKey","StoreName","City","Region"],
          STORES)

write_csv("dim_product.csv",
          ["ProductKey","ProductName","Category","Brand"],
          PRODUCTS)

write_csv("dim_supplier.csv",
          ["SupplierKey","SupplierName","ContactInfo"],
          SUPPLIERS)

write_csv("dim_customer.csv",
          ["CustomerKey","CustomerID","FirstName","LastName","Segment","City","ValidFrom","ValidTo"],
          CUSTOMERS)

write_csv("dim_payment.csv",
          ["PaymentKey","PaymentType"],
          PAYMENTS)

write_csv("fact_sales.csv",
          ["SaleID","DateKey","StoreKey","ProductKey","SupplierKey","CustomerKey","PaymentKey","Quantity","SalesAmount","FullDate"],
          fact_sales)

print("Valmis.")
