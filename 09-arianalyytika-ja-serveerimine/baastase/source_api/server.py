"""Kohalik veebipoe sündmuste API 9. praktikumi jaoks.

See teenus on andmeallikas. Ta ei kirjuta ise andmebaasi.
ETL töövoog küsib siit müügisündmuseid ja maandab need `staging` kihti.

Sündmuste päevane muster järgib sama mõtet nagu 4. praktikumi kohalik API:

* sama sisend annab alati sama andmestiku;
* päevane sündmuste arv kõigub umbes saja sündmuse ümber;
* sündmused koonduvad rohkem õhtusesse aega.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
from math import cos, log, pi, sqrt
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo


HOST = "0.0.0.0"
PORT = int(os.environ.get("SOURCE_API_PORT", "8019"))
LOCAL_TZ_NAME = os.environ.get("TZ", "Europe/Tallinn")
TALLINN_TZ = ZoneInfo(LOCAL_TZ_NAME)
SOURCE_DATA_DIR = Path(os.environ.get("SOURCE_DATA_DIR", "/app/source_data"))
SOURCE_START_DATE = date.fromisoformat(os.environ.get("DEMO_START_DATE", "2026-04-30"))
SOURCE_MAX_DAYS = int(os.environ.get("SOURCE_MAX_DAYS", "120"))
SEED_PREFIX = "praktikum-09-base-source-api"

AVERAGE_ORDERS_PER_DAY = int(os.environ.get("SOURCE_AVERAGE_ORDERS_PER_DAY", "100"))
ORDERS_PER_DAY_STDDEV = int(os.environ.get("SOURCE_ORDERS_PER_DAY_STDDEV", "10"))
ORDER_COUNT_MIN = int(os.environ.get("SOURCE_ORDER_COUNT_MIN", "70"))
ORDER_COUNT_MAX = int(os.environ.get("SOURCE_ORDER_COUNT_MAX", "130"))
ORDER_TIME_MEAN_MINUTES = 18 * 60
ORDER_TIME_STDDEV_MINUTES = 2 * 60
MINUTES_PER_DAY = 24 * 60


def stable_int(seed: str, minimum: int, maximum: int) -> int:
    """Tagasta sama sisendi jaoks alati sama täisarv.

    Nii tekib sünteetiline andmestik uuesti käivitamisel samasugusena.
    """
    span = maximum - minimum + 1
    seeded_text = f"{SEED_PREFIX}|{seed}"
    value = int(sha256(seeded_text.encode("utf-8")).hexdigest()[:8], 16)
    return minimum + (value % span)


def stable_fraction(seed: str) -> float:
    """Tagasta sama sisendi jaoks alati sama murdarv vahemikus 0 kuni 1."""
    seeded_text = f"{SEED_PREFIX}|{seed}"
    value = int(sha256(seeded_text.encode("utf-8")).hexdigest()[:16], 16)
    return (value + 0.5) / (16**16)


def stable_gaussian(seed: str, mean: float, stddev: float) -> float:
    """Tekita kellukakujulise jaotusega väärtus.

    Kasutame seda päevase tellimuste arvu ja tellimuse kellaaja jaoks.
    """
    u1 = stable_fraction(f"{seed}|u1")
    u2 = stable_fraction(f"{seed}|u2")
    z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * pi * u2)
    return mean + (stddev * z0)


def read_csv_dicts(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_products() -> list[dict]:
    """Loe tootekataloog failist, et API saaks sündmustele toote lisada."""
    return read_csv_dicts(SOURCE_DATA_DIR / "products.csv")


def load_stores() -> list[dict]:
    """Loe poodide loend failist, et API saaks sündmustele piirkonna lisada."""
    return read_csv_dicts(SOURCE_DATA_DIR / "stores.csv")


def source_end_date() -> date:
    """Tagasta viimane kuupäev, mille kohta API oskab andmeid arvutada."""
    return SOURCE_START_DATE + timedelta(days=SOURCE_MAX_DAYS - 1)


def now_local() -> datetime:
    """Tagasta praegune aeg praktikumi kohalikus ajavööndis."""
    return datetime.now(TALLINN_TZ)


def parse_event_time(value: str) -> datetime:
    """Muuda API vastuses olev ISO-kujul ajatempel Pythoni ajaks."""
    return datetime.fromisoformat(value)


def get_order_count(logical_date: date) -> int:
    """Arvuta ühe päeva tellimuste arv.

    Mudel hoiab päevase mahu umbes saja tellimuse juures, kuid laseb sellel
    natuke kõikuda. Alumine ja ülemine piir tulevad `.env` failist.
    """
    count = round(
        stable_gaussian(
            f"{logical_date.isoformat()}|order_count",
            AVERAGE_ORDERS_PER_DAY,
            ORDERS_PER_DAY_STDDEV,
        )
    )
    return max(ORDER_COUNT_MIN, min(ORDER_COUNT_MAX, count))


def count_events_before(logical_date: date) -> int:
    """Leia, mitu sündmust on varasematel päevadel kokku olnud."""
    total = 0
    current_date = SOURCE_START_DATE
    while current_date < logical_date:
        total += get_order_count(current_date)
        current_date += timedelta(days=1)
    return total


def date_for_sequence(event_sequence: int) -> date:
    """Leia, millisele kuupäevale etteantud järjekorranumbriga sündmus kuulub."""
    if event_sequence < 1:
        raise ValueError("event_sequence peab olema vähemalt 1.")

    current_date = SOURCE_START_DATE
    remaining = event_sequence
    while current_date <= source_end_date():
        day_count = get_order_count(current_date)
        if remaining <= day_count:
            return current_date
        remaining -= day_count
        current_date += timedelta(days=1)

    raise ValueError("event_sequence jääb allika vahemikust välja.")


def build_orders(logical_date: date) -> list[dict]:
    """Koosta ühe päeva sünteetilised tellimused.

    API ei salvesta sündmusi faili ega andmebaasi. Ta arvutab need vajaduse
    korral uuesti samade reeglite järgi.
    """
    products = load_products()
    stores = load_stores()
    day_count = get_order_count(logical_date)
    sequence_before_day = count_events_before(logical_date)
    raw_orders = []

    for order_no in range(1, day_count + 1):
        product = products[
            stable_int(
                f"{logical_date.isoformat()}|product|{order_no}",
                0,
                len(products) - 1,
            )
        ]
        store = stores[
            stable_int(
                f"{logical_date.isoformat()}|store|{order_no}",
                0,
                len(stores) - 1,
            )
        ]
        quantity = stable_int(f"{logical_date.isoformat()}|quantity|{order_no}", 1, 5)
        cents_step = stable_int(f"{logical_date.isoformat()}|price|{order_no}", 0, 6)
        unit_price = (
            Decimal(product["base_price_eur"])
            + Decimal(cents_step) * Decimal("0.50")
        ).quantize(
            Decimal("0.01"),
        )
        minute_of_day = round(
            stable_gaussian(
                f"{logical_date.isoformat()}|order_time|{order_no}",
                ORDER_TIME_MEAN_MINUTES,
                ORDER_TIME_STDDEV_MINUTES,
            )
        ) % MINUTES_PER_DAY
        event_time = datetime.combine(
            logical_date,
            time(minute_of_day // 60, minute_of_day % 60),
            tzinfo=TALLINN_TZ,
        )
        raw_orders.append(
            {
                "event_time": event_time,
                "store_id": store["store_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price_eur": str(unit_price),
                "_order_no": order_no,
            }
        )

    raw_orders.sort(
        key=lambda order: (
            order["event_time"],
            order["store_id"],
            order["product_id"],
            order["_order_no"],
        )
    )

    # Sorteerimise järel saab iga sündmus püsiva järjekorranumbri.
    # ETL kasutab seda numbrit järjehoidjana.
    orders = []
    for index, raw_order in enumerate(raw_orders, start=1):
        event_sequence = sequence_before_day + index
        orders.append(
            {
                "event_id": f"EVT-{event_sequence:09d}",
                "event_sequence": event_sequence,
                "order_id": f"ORD-{logical_date.strftime('%Y%m%d')}-{index:03d}",
                "event_time": raw_order["event_time"].isoformat(),
                "store_id": raw_order["store_id"],
                "product_id": raw_order["product_id"],
                "quantity": raw_order["quantity"],
                "unit_price_eur": raw_order["unit_price_eur"],
                "source": "source-api",
            }
        )
    return orders


def count_available_events(as_of: datetime) -> int:
    """Leia, mitu sündmust on etteantud hetkeks kättesaadavaks muutunud.

    API võib arvutada kogu sünteetilise andmestiku ette, kuid päringu vastusesse
    lubame ainult need sündmused, mille `event_time` ei ole tulevikus.
    """
    total = 0
    current_date = SOURCE_START_DATE

    while current_date < as_of.date() and current_date <= source_end_date():
        total += get_order_count(current_date)
        current_date += timedelta(days=1)

    if SOURCE_START_DATE <= as_of.date() <= source_end_date():
        total += sum(
            1
            for event in build_orders(as_of.date())
            if parse_event_time(event["event_time"]) <= as_of
        )

    return total


def build_events_after(
    after_sequence: int,
    limit: int,
    *,
    as_of: datetime | None = None,
    available_sequence: int | None = None,
) -> list[dict]:
    """Tagasta järgmine ports sündmuseid pärast antud järjekorranumbrit.

    `after_sequence` on API järjehoidja. Kui ETL on jõudnud sündmuseni 1377,
    küsib ta järgmisena sündmuseid pärast 1377. `limit` ütleb, mitu rida API
    korraga kõige rohkem tagasi annab. `as_of` hoiab ära tuleviku sündmused.
    """
    if limit < 1:
        return []

    as_of = as_of or now_local()
    if available_sequence is None:
        available_sequence = count_available_events(as_of)
    if after_sequence >= available_sequence:
        return []

    target_sequence = after_sequence + 1
    effective_limit = min(limit, available_sequence - after_sequence)
    events: list[dict] = []
    while len(events) < effective_limit:
        try:
            current_date = date_for_sequence(target_sequence)
        except ValueError:
            break

        for event in build_orders(current_date):
            if after_sequence < event["event_sequence"] <= available_sequence:
                events.append(event)
                if len(events) >= effective_limit:
                    break
        target_sequence = events[-1]["event_sequence"] + 1 if events else target_sequence + 1

    return events


def backfill_state(days: int, *, as_of: datetime | None = None) -> dict:
    """Kirjelda, kuhu algne ajaloo laadimine valitud päevade arvuga jõuab.

    Kui soovitud ajaloo lõpp oleks praegusest hetkest tulevikus, lõikame piiri
    viimase kättesaadava sündmuse juurde. Nii ei jäta ETL järjehoidja tuleviku
    sündmuseid kogemata vahele.
    """
    as_of = as_of or now_local()
    days = max(1, min(days, SOURCE_MAX_DAYS))
    requested_through_date = SOURCE_START_DATE + timedelta(days=days - 1)
    requested_through_sequence = count_events_before(requested_through_date + timedelta(days=1))
    available_sequence = count_available_events(as_of)
    through_sequence = min(requested_through_sequence, available_sequence)
    through_date = date_for_sequence(through_sequence) if through_sequence > 0 else None
    next_events = build_events_after(
        through_sequence,
        1,
        as_of=as_of,
        available_sequence=available_sequence,
    )
    return {
        "days": days,
        "from_date": SOURCE_START_DATE.isoformat(),
        "through_date": through_date.isoformat() if through_date else None,
        "through_sequence": through_sequence,
        "next_event_time": next_events[0]["event_time"] if next_events else None,
        "requested_through_date": requested_through_date.isoformat(),
        "requested_through_sequence": requested_through_sequence,
        "available_as_of": as_of.isoformat(),
        "available_through_sequence": available_sequence,
        "capped_by_current_time": through_sequence < requested_through_sequence,
    }


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP päringute töötleja.

    Pythoni standardteegi `BaseHTTPRequestHandler` annab meile raami ette.
    Meie kirjeldame siin, mida API vastab teedel `/health`,
    `/api/backfill-state` ja `/api/events`.
    """

    server_version = "Praktikum09SourceAPI/1.0"

    def _send_json(self, status_code: int, payload: dict) -> None:
        """Saada kliendile JSON vastus."""
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_html(self, status_code: int, html: str) -> None:
        """Saada kliendile brauseris loetav HTML leht."""
        encoded = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _build_docs_page(self) -> str:
        """Ehita API avaleht, kust õppija näeb teenuse hetkeseisu."""
        as_of = now_local()
        state = backfill_state(14, as_of=as_of)
        return f"""<!doctype html>
<html lang="et">
  <head>
    <meta charset="utf-8">
    <title>Praktikum 9 Source API</title>
  </head>
  <body>
    <h1>Praktikum 9 Source API</h1>
    <p>See teenus simuleerib veebipoe müügisündmuste allikat.</p>
    <ul>
      <li>Andmeid alates: {SOURCE_START_DATE.isoformat()}</li>
      <li>Genereerimise ülempiir: {source_end_date().isoformat()}</li>
      <li>API kohalik aeg: {as_of.isoformat(timespec="seconds")}</li>
      <li>Praeguseks kättesaadav kuni sündmuseni: {state["available_through_sequence"]}</li>
      <li>14 päeva backfill lõpeb sündmusel: {state["through_sequence"]}</li>
    </ul>
    <p><a href="/health">/health</a></p>
    <p><a href="/api/events?after_sequence=0&amp;limit=12">/api/events?after_sequence=0&amp;limit=12</a></p>
    <p><a href="/api/backfill-state?days=14">/api/backfill-state?days=14</a></p>
  </body>
</html>
"""

    def log_message(self, fmt: str, *args) -> None:
        print(f"[source-api] {self.address_string()} - {fmt % args}", flush=True)

    def do_GET(self) -> None:
        """Vasta GET päringutele.

        Olulised teed on `/health`, `/api/backfill-state` ja `/api/events`.
        """
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in {"/", "/docs"}:
            self._send_html(200, self._build_docs_page())
            return

        if parsed.path == "/health":
            as_of = now_local()
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "praktikum-09-source-api",
                    "available_from": SOURCE_START_DATE.isoformat(),
                    "available_to": source_end_date().isoformat(),
                    "available_as_of": as_of.isoformat(),
                    "available_through_sequence": count_available_events(as_of),
                    "average_orders_per_day": AVERAGE_ORDERS_PER_DAY,
                },
            )
            return

        if parsed.path == "/api/backfill-state":
            try:
                days = int(query.get("days", ["14"])[0])
            except ValueError:
                self._send_json(400, {"message": "days peab olema täisarv."})
                return
            self._send_json(200, backfill_state(days))
            return

        if parsed.path == "/api/events":
            try:
                after_sequence = int(query.get("after_sequence", ["0"])[0])
                limit = int(query.get("limit", ["12"])[0])
            except ValueError:
                self._send_json(400, {"message": "after_sequence ja limit peavad olema täisarvud."})
                return

            # API kaitseb end liiga suure päringu eest. Tavaline mikrobatch'i
            # suurus tuleb scheduler'i `.env` failist ja on vaikimisi 12.
            limit = max(1, min(limit, 1000))
            as_of = now_local()
            available_sequence = count_available_events(as_of)
            events = build_events_after(
                after_sequence,
                limit,
                as_of=as_of,
                available_sequence=available_sequence,
            )
            next_after_sequence = events[-1]["event_sequence"] if events else after_sequence
            self._send_json(
                200,
                {
                    "dataset": "synthetic-webshop-events",
                    "after_sequence": after_sequence,
                    "limit": limit,
                    "returned_count": len(events),
                    "next_after_sequence": next_after_sequence,
                    "has_more": bool(
                        build_events_after(
                            next_after_sequence,
                            1,
                            as_of=as_of,
                            available_sequence=available_sequence,
                        )
                    ),
                    "available_as_of": as_of.isoformat(),
                    "available_through_sequence": available_sequence,
                    "events": events,
                },
            )
            return

        self._send_json(404, {"message": "Tundmatu tee."})


def main() -> None:
    server = HTTPServer((HOST, PORT), RequestHandler)
    print(
        f"[source-api] Käivitus aadressil http://{HOST}:{PORT} "
        f"(andmed {SOURCE_START_DATE.isoformat()} kuni {source_end_date().isoformat()})",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
