"""Sünteetilise veebipoe mikrobatch töövoog.

Skript teeb kaks tööd:

* `bootstrap` laadib dimensioonid ja loob algse ajaloo;
* `run-scheduled` lisab väikese koguse uusi müügisündmusi.

Cron käivitab `run-scheduled` käsu iga minuti järel. Superset loeb samu tabeleid
ja vaateid, seega on dashboardil näha nii müügiandmete kui ka töövoo logi muutus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2


TALLINN_TZ = ZoneInfo("Europe/Tallinn")
SOURCE_DATA_DIR = Path(os.environ.get("SOURCE_DATA_DIR", "/app/source_data"))
STATE_KEY = "sales_stream"


@dataclass(frozen=True)
class Product:
    product_id: str
    product_name: str
    category: str
    base_price_eur: Decimal


@dataclass(frozen=True)
class Store:
    store_id: str
    store_name: str
    city: str
    region: str


def env_text(name: str, default: str) -> str:
    return os.environ.get(name, default)


def env_int(name: str, default: int) -> int:
    return int(env_text(name, str(default)))


def now_local() -> datetime:
    return datetime.now(TALLINN_TZ)


def log(message: str) -> None:
    print(f"{now_local().isoformat()} | {message}", flush=True)


def get_connection():
    return psycopg2.connect(
        host=env_text("DB_HOST", "db"),
        port=env_text("DB_PORT", "5432"),
        user=env_text("DB_USER", "praktikum"),
        password=env_text("DB_PASSWORD", "praktikum"),
        dbname=env_text("DB_NAME", "praktikum"),
    )


def stable_int(seed: str, minimum: int, maximum: int) -> int:
    span = maximum - minimum + 1
    value = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12], 16)
    return minimum + (value % span)


def read_products() -> list[Product]:
    with (SOURCE_DATA_DIR / "products.csv").open(encoding="utf-8", newline="") as handle:
        return [
            Product(
                product_id=row["product_id"],
                product_name=row["product_name"],
                category=row["category"],
                base_price_eur=Decimal(row["base_price_eur"]),
            )
            for row in csv.DictReader(handle)
        ]


def read_stores() -> list[Store]:
    with (SOURCE_DATA_DIR / "stores.csv").open(encoding="utf-8", newline="") as handle:
        return [
            Store(
                store_id=row["store_id"],
                store_name=row["store_name"],
                city=row["city"],
                region=row["region"],
            )
            for row in csv.DictReader(handle)
        ]


def load_dimensions(conn, products: list[Product], stores: list[Store]) -> None:
    loaded_at = now_local()
    with conn.cursor() as cur:
        for product in products:
            cur.execute(
                """
                INSERT INTO staging.products_raw (
                    product_id,
                    product_name,
                    category,
                    base_price_eur,
                    loaded_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    category = EXCLUDED.category,
                    base_price_eur = EXCLUDED.base_price_eur,
                    loaded_at = EXCLUDED.loaded_at
                """,
                (
                    product.product_id,
                    product.product_name,
                    product.category,
                    product.base_price_eur,
                    loaded_at,
                ),
            )

        for store in stores:
            cur.execute(
                """
                INSERT INTO staging.stores_raw (
                    store_id,
                    store_name,
                    city,
                    region,
                    loaded_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (store_id) DO UPDATE SET
                    store_name = EXCLUDED.store_name,
                    city = EXCLUDED.city,
                    region = EXCLUDED.region,
                    loaded_at = EXCLUDED.loaded_at
                """,
                (store.store_id, store.store_name, store.city, store.region, loaded_at),
            )


def normalize_shop_time(value: datetime) -> datetime:
    """Hoia simuleeritud sündmused enamasti veebipoe aktiivses päevas."""
    if value.hour >= 22:
        next_day = value.date() + timedelta(days=1)
        return datetime.combine(next_day, time(8, 0), tzinfo=TALLINN_TZ)
    if value.hour < 8:
        return datetime.combine(value.date(), time(8, 0), tzinfo=TALLINN_TZ)
    return value


def build_order(
    *,
    event_sequence: int,
    event_time: datetime,
    products: list[Product],
    stores: list[Store],
    run_id: uuid.UUID,
    is_backfill: bool,
) -> dict:
    product = products[stable_int(f"product-{event_sequence}", 0, len(products) - 1)]
    store = stores[stable_int(f"store-{event_sequence}", 0, len(stores) - 1)]
    quantity = stable_int(f"quantity-{event_sequence}", 1, 5)
    price_step = Decimal(stable_int(f"price-{event_sequence}", 0, 5)) * Decimal("0.50")
    unit_price = (product.base_price_eur + price_step).quantize(Decimal("0.01"))

    return {
        "event_id": f"EVT-{event_sequence:09d}",
        "event_sequence": event_sequence,
        "order_id": f"ORD-{event_time.strftime('%Y%m%d')}-{event_sequence:09d}",
        "event_time": event_time,
        "processed_at": now_local(),
        "store_id": store.store_id,
        "product_id": product.product_id,
        "quantity": quantity,
        "unit_price_eur": unit_price,
        "source_batch_id": str(run_id),
        "is_backfill": is_backfill,
    }


def insert_orders(conn, orders: list[dict]) -> int:
    inserted = 0
    with conn.cursor() as cur:
        for order in orders:
            cur.execute(
                """
                INSERT INTO staging.order_events (
                    event_id,
                    event_sequence,
                    order_id,
                    event_time,
                    processed_at,
                    store_id,
                    product_id,
                    quantity,
                    unit_price_eur,
                    source_batch_id,
                    is_backfill
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    order["event_id"],
                    order["event_sequence"],
                    order["order_id"],
                    order["event_time"],
                    order["processed_at"],
                    order["store_id"],
                    order["product_id"],
                    order["quantity"],
                    order["unit_price_eur"],
                    order["source_batch_id"],
                    order["is_backfill"],
                ),
            )
            inserted += cur.rowcount
    return inserted


def insert_run_log(
    conn,
    *,
    run_id: uuid.UUID,
    run_type: str,
    status: str,
    rows_inserted: int,
    watermark_from: datetime | None,
    watermark_to: datetime | None,
    message: str,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO monitoring.microbatch_run_log (
                run_id,
                run_type,
                status,
                rows_inserted,
                watermark_from,
                watermark_to,
                message,
                started_at,
                finished_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(run_id),
                run_type,
                status,
                rows_inserted,
                watermark_from,
                watermark_to,
                message,
                started_at,
                finished_at,
            ),
        )


def initialize_state(conn, *, next_sequence: int, next_event_time: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO control.pipeline_state (
                state_key,
                next_event_sequence,
                next_event_time,
                updated_at
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (state_key) DO UPDATE SET
                next_event_sequence = GREATEST(
                    control.pipeline_state.next_event_sequence,
                    EXCLUDED.next_event_sequence
                ),
                next_event_time = GREATEST(
                    control.pipeline_state.next_event_time,
                    EXCLUDED.next_event_time
                ),
                updated_at = EXCLUDED.updated_at
            """,
            (STATE_KEY, next_sequence, next_event_time, now_local()),
        )


def bootstrap(_args: argparse.Namespace) -> None:
    run_id = uuid.uuid4()
    started_at = now_local()
    products = read_products()
    stores = read_stores()
    demo_start_date = date.fromisoformat(env_text("DEMO_START_DATE", "2026-04-01"))
    backfill_days = env_int("INITIAL_BACKFILL_DAYS", 14)
    orders_per_day = env_int("INITIAL_ORDERS_PER_DAY", 80)
    orders: list[dict] = []

    for day_offset in range(backfill_days):
        current_date = demo_start_date + timedelta(days=day_offset)
        for order_no in range(orders_per_day):
            event_sequence = (day_offset * orders_per_day) + order_no + 1
            minute_of_day = stable_int(
                f"{current_date.isoformat()}-{order_no}-minute",
                8 * 60,
                21 * 60,
            )
            event_time = datetime.combine(
                current_date,
                time(minute_of_day // 60, minute_of_day % 60),
                tzinfo=TALLINN_TZ,
            )
            orders.append(
                build_order(
                    event_sequence=event_sequence,
                    event_time=event_time,
                    products=products,
                    stores=stores,
                    run_id=run_id,
                    is_backfill=True,
                )
            )

    next_sequence = (backfill_days * orders_per_day) + 1
    next_event_time = datetime.combine(
        demo_start_date + timedelta(days=backfill_days),
        time(8, 0),
        tzinfo=TALLINN_TZ,
    )

    conn = get_connection()
    try:
        load_dimensions(conn, products, stores)
        inserted = insert_orders(conn, orders)
        initialize_state(
            conn,
            next_sequence=next_sequence,
            next_event_time=next_event_time,
        )
        finished_at = now_local()
        insert_run_log(
            conn,
            run_id=run_id,
            run_type="bootstrap",
            status="success",
            rows_inserted=inserted,
            watermark_from=min(order["event_time"] for order in orders),
            watermark_to=max(order["event_time"] for order in orders),
            message=f"Alglaadimine valmis: {inserted} uut müügisündmust.",
            started_at=started_at,
            finished_at=finished_at,
        )
        conn.commit()
        log(f"Alglaadimine valmis. Lisatud ridu: {inserted}.")
    except Exception as exc:
        conn.rollback()
        finished_at = now_local()
        insert_run_log(
            conn,
            run_id=run_id,
            run_type="bootstrap",
            status="error",
            rows_inserted=0,
            watermark_from=None,
            watermark_to=None,
            message=str(exc),
            started_at=started_at,
            finished_at=finished_at,
        )
        conn.commit()
        raise
    finally:
        conn.close()


def run_scheduled(_args: argparse.Namespace) -> None:
    run_id = uuid.uuid4()
    started_at = now_local()
    products = read_products()
    stores = read_stores()
    batch_size = env_int("MICROBATCH_SIZE", 12)
    step_minutes = env_int("MICROBATCH_EVENT_STEP_MINUTES", 5)

    conn = get_connection()
    try:
        load_dimensions(conn, products, stores)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT next_event_sequence, next_event_time
                FROM control.pipeline_state
                WHERE state_key = %s
                FOR UPDATE
                """,
                (STATE_KEY,),
            )
            state_row = cur.fetchone()

            if state_row is None:
                fallback_time = datetime.combine(date.today(), time(8, 0), tzinfo=TALLINN_TZ)
                initialize_state(conn, next_sequence=1, next_event_time=fallback_time)
                next_sequence = 1
                next_event_time = fallback_time
            else:
                next_sequence = int(state_row[0])
                next_event_time = state_row[1].astimezone(TALLINN_TZ)

            orders = []
            current_event_time = normalize_shop_time(next_event_time)
            for offset in range(batch_size):
                event_sequence = next_sequence + offset
                event_time = normalize_shop_time(current_event_time)
                orders.append(
                    build_order(
                        event_sequence=event_sequence,
                        event_time=event_time,
                        products=products,
                        stores=stores,
                        run_id=run_id,
                        is_backfill=False,
                    )
                )
                current_event_time = normalize_shop_time(
                    event_time + timedelta(minutes=step_minutes)
                )

            inserted = insert_orders(conn, orders)
            cur.execute(
                """
                UPDATE control.pipeline_state
                SET
                    next_event_sequence = %s,
                    next_event_time = %s,
                    updated_at = %s
                WHERE state_key = %s
                """,
                (
                    next_sequence + batch_size,
                    current_event_time,
                    now_local(),
                    STATE_KEY,
                ),
            )

        finished_at = now_local()
        insert_run_log(
            conn,
            run_id=run_id,
            run_type="scheduled",
            status="success",
            rows_inserted=inserted,
            watermark_from=orders[0]["event_time"],
            watermark_to=orders[-1]["event_time"],
            message=f"Cron lisas {inserted} uut müügisündmust.",
            started_at=started_at,
            finished_at=finished_at,
        )
        conn.commit()
        log(f"Cron mikrobatch valmis. Lisatud ridu: {inserted}.")
    except Exception as exc:
        conn.rollback()
        finished_at = now_local()
        insert_run_log(
            conn,
            run_id=run_id,
            run_type="scheduled",
            status="error",
            rows_inserted=0,
            watermark_from=None,
            watermark_to=None,
            message=str(exc),
            started_at=started_at,
            finished_at=finished_at,
        )
        conn.commit()
        raise
    finally:
        conn.close()


def check(_args: argparse.Namespace) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for label, query in [
                ("tooted", "SELECT COUNT(*) FROM staging.products_raw"),
                ("poed", "SELECT COUNT(*) FROM staging.stores_raw"),
                ("müügisündmused", "SELECT COUNT(*) FROM staging.order_events"),
                ("logiread", "SELECT COUNT(*) FROM monitoring.microbatch_run_log"),
            ]:
                cur.execute(query)
                print(f"{label}: {cur.fetchone()[0]}")
    finally:
        conn.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Praktikum 9 mikrobatch töövoog")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap", help="Lae dimensioonid ja loo algne ajalugu")
    subparsers.add_parser("run-scheduled", help="Lisa üks cron'i mikrobatch")
    subparsers.add_parser("check", help="Prindi lühike seisukontroll")

    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    if args.command == "bootstrap":
        bootstrap(args)
    elif args.command == "run-scheduled":
        run_scheduled(args)
    elif args.command == "check":
        check(args)
    else:
        raise ValueError(f"Tundmatu käsk: {args.command}")


if __name__ == "__main__":
    main(sys.argv[1:])
