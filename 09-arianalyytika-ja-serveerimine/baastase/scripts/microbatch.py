"""Sünteetilise veebipoe mikrobatch töövoog.

Skript teeb kaks tööd:

* `bootstrap` laadib dimensioonid ja toob source API-st algse ajaloo;
* `run-scheduled` toob source API-st järgmise väikese koguse müügisündmusi.

Cron käivitab `run-scheduled` käsu iga minuti järel. Superset loeb samu tabeleid
ja vaateid, seega on dashboardil näha nii müügiandmete kui ka töövoo logi muutus.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
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
    """Loe keskkonnamuutuja tekstina.

    Docker Compose annab skriptile `.env` failist väärtused kaasa.
    Kui väärtust ei ole seatud, kasutame praktikumi jaoks sobivat vaikeväärtust.
    """
    return os.environ.get(name, default)


def env_int(name: str, default: int) -> int:
    return int(env_text(name, str(default)))


def now_local() -> datetime:
    return datetime.now(TALLINN_TZ)


def log(message: str) -> None:
    print(f"{now_local().isoformat()} | {message}", flush=True)


def get_connection():
    """Ava ühendus PostgreSQL andmebaasi.

    Skript töötab scheduler'i konteineris. Sealt ei kasutata `localhost` aadressi,
    vaid Docker Compose teenuse nime `db`.
    """
    return psycopg2.connect(
        host=env_text("DB_HOST", "db"),
        port=env_text("DB_PORT", "5432"),
        user=env_text("DB_USER", "praktikum"),
        password=env_text("DB_PASSWORD", "praktikum"),
        dbname=env_text("DB_NAME", "praktikum"),
    )


def read_products() -> list[Product]:
    """Loe tootekataloog CSV failist.

    Need read on dimensiooniandmed: nad kirjeldavad toodet, mitte üksikut müüki.
    """
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
    """Lae tooted ja poed staging kihti.

    `ON CONFLICT` teeb laadimise idempotentseks: sama faili võib uuesti laadida
    ilma duplikaatridu tekitamata.
    """
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


def get_source_api_url() -> str:
    return env_text("SOURCE_API_URL", "http://source-api:8019").rstrip("/")


def fetch_json(path: str, params: dict) -> dict:
    query = urlencode(params)
    url = f"{get_source_api_url()}{path}?{query}" if query else f"{get_source_api_url()}{path}"
    with urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_source_events(*, after_sequence: int, limit: int) -> dict:
    """Küsi järgmised sündmused pärast etteantud järjekorranumbrit.

    `after_sequence` toimib siin nagu väike offset ehk järjehoidja.
    `limit` ütleb, mitu sündmust üks mikrobatch kõige rohkem vastu võtab.
    """
    return fetch_json(
        "/api/events",
        {
            "after_sequence": after_sequence,
            "limit": limit,
        },
    )


def fetch_backfill_state(days: int) -> dict:
    return fetch_json("/api/backfill-state", {"days": days})


def parse_event_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def insert_orders(conn, orders: list[dict]) -> int:
    """Kirjuta müügisündmused staging tabelisse.

    `event_id` on primaarvõti. Kui sama sündmus jõuab skriptini teist korda,
    jätab `ON CONFLICT DO NOTHING` selle vahele.
    """
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
                    parse_event_time(order["event_time"]),
                    now_local(),
                    order["store_id"],
                    order["product_id"],
                    order["quantity"],
                    Decimal(str(order["unit_price_eur"])),
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
    """Kirjuta töövoo käivituse kokkuvõte logitabelisse.

    Superset loeb seda tabelit dashboardil. Nii näeb õppija veebiliidesest,
    kas cron töötab ja kui palju ridu viimane mikrobatch lisas.
    """
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
    """Sea töövoo järjehoidja.

    `control.pipeline_state` ütleb järgmisele cron käivitusele, millisest
    sündmusest jätkata. `GREATEST` kaitseb selle eest, et järjehoidja ei liiguks
    kogemata tagasi.
    """
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
    """Lae algne ajalugu ja sea scheduler valmis järgmiseks sündmuseks."""
    run_id = uuid.uuid4()
    started_at = now_local()
    products = read_products()
    stores = read_stores()
    backfill_days = env_int("INITIAL_BACKFILL_DAYS", 14)
    backfill_info = fetch_backfill_state(backfill_days)
    through_sequence = int(backfill_info["through_sequence"])
    next_event_time = (
        parse_event_time(backfill_info["next_event_time"])
        if backfill_info["next_event_time"]
        else now_local()
    )
    source_batch_limit = 500
    orders: list[dict] = []
    after_sequence = 0

    # Alglaadimine võib võtta rohkem ridu kui tavaline ühe minuti mikrobatch.
    # Seepärast küsime ajaloo source API-st suuremate tükkidena.
    while after_sequence < through_sequence:
        response = fetch_source_events(
            after_sequence=after_sequence,
            limit=min(source_batch_limit, through_sequence - after_sequence),
        )
        source_events = response["events"]
        if not source_events:
            break
        for event in source_events:
            event["source_batch_id"] = str(run_id)
            event["is_backfill"] = True
        orders.extend(source_events)
        after_sequence = int(response["next_after_sequence"])

    conn = get_connection()
    try:
        load_dimensions(conn, products, stores)
        inserted = insert_orders(conn, orders)
        initialize_state(
            conn,
            next_sequence=through_sequence + 1,
            next_event_time=next_event_time,
        )
        finished_at = now_local()
        insert_run_log(
            conn,
            run_id=run_id,
            run_type="bootstrap",
            status="success",
            rows_inserted=inserted,
            watermark_from=min(parse_event_time(order["event_time"]) for order in orders),
            watermark_to=max(parse_event_time(order["event_time"]) for order in orders),
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
    """Lisa üks regulaarne mikrobatch.

    Cron käivitab selle funktsiooni iga minuti järel. Partii suurus tuleb
    `.env` failis olevast `MICROBATCH_SIZE` väärtusest.
    """
    run_id = uuid.uuid4()
    started_at = now_local()
    products = read_products()
    stores = read_stores()
    batch_size = env_int("MICROBATCH_SIZE", 12)

    conn = get_connection()
    try:
        load_dimensions(conn, products, stores)
        with conn.cursor() as cur:
            # `FOR UPDATE` lukustab järjehoidja rea selle tehingu ajaks.
            # See on sama mõte nagu ühel töötegijal märkida, millise kaustani ta
            # jõudis, et teine töö ei alustaks samast kohast.
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
                next_sequence = 1
                next_event_time = now_local()
                initialize_state(conn, next_sequence=next_sequence, next_event_time=next_event_time)
            else:
                next_sequence = int(state_row[0])
                next_event_time = state_row[1].astimezone(TALLINN_TZ)

            # Siin rakendubki mikrobatch'i suurus. Kui allikas pakub rohkem
            # sündmusi, jäävad need järgmise cron käivituse ootele.
            response = fetch_source_events(
                after_sequence=next_sequence - 1,
                limit=batch_size,
            )
            orders = response["events"]
            for event in orders:
                event["source_batch_id"] = str(run_id)
                event["is_backfill"] = False

            if not orders:
                finished_at = now_local()
                insert_run_log(
                    conn,
                    run_id=run_id,
                    run_type="scheduled",
                    status="skipped",
                    rows_inserted=0,
                    watermark_from=None,
                    watermark_to=None,
                    message="Source API ei tagastanud uusi sündmusi.",
                    started_at=started_at,
                    finished_at=finished_at,
                )
                conn.commit()
                log("Cron mikrobatch jättis töö vahele: uusi sündmusi ei olnud.")
                return

            inserted = insert_orders(conn, orders)
            next_after_sequence = int(response["next_after_sequence"])

            # Järgmise sündmuse aeg aitab dashboardil näidata, kui kaugele
            # andmeajas järgmine töö võiks liikuda.
            next_events = fetch_source_events(after_sequence=next_after_sequence, limit=1)["events"]
            next_event_time = (
                parse_event_time(next_events[0]["event_time"])
                if next_events
                else parse_event_time(orders[-1]["event_time"])
            )
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
                    next_after_sequence + 1,
                    next_event_time,
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
            watermark_from=parse_event_time(orders[0]["event_time"]),
            watermark_to=parse_event_time(orders[-1]["event_time"]),
            message=(
                f"Cron laadis source API-st {inserted} sündmust. "
                f"Batch'i piirang oli {batch_size}."
            ),
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
