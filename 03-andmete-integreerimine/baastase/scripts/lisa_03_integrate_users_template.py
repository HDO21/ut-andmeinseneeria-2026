"""Lisaülesande näide kolme allika ETL töövoost.

Extract:
- loe kasutajad API-st
- loe teavituseelistused JSON failist
- loe kasutajastaatused staging.user_status tabelist

Transform:
- puhasta e-posti aadress
- ühenda API, CSV ja JSON andmed ühe võtme alusel

Load:
- salvesta API toorandmed staging.api_users tabelisse
- salvesta JSON andmed staging.notification_preferences tabelisse
- salvesta lõpptulemus analytics.user_profile tabelisse
"""

import json
import os

import psycopg2
import requests


API_URL = "https://jsonplaceholder.typicode.com/users"
PREFERENCES_PATH = "/data/teavituseelistused.json"

# See lisaülesande skript eeldab, et oled enne käivitanud faili
# /scripts/lisa_01_prepare_preferences.sql.


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "praktikum"),
        password=os.environ.get("DB_PASSWORD", "praktikum"),
        dbname=os.environ.get("DB_NAME", "praktikum"),
    )


def normalize_email(value):
    """Transform: muuda e-post ühendamiseks sobivaks.

    TODO:
    1. Kui väärtus on None, tagasta None.
    2. Eemalda algusest ja lõpust tühikud.
    3. Muuda tulemus väikesteks tähtedeks.
    """
    raise NotImplementedError("Tee normalize_email funktsioon valmis.")


def fetch_api_users():
    """Extract: too kasutajad API-st ja jäta alles vajalikud väljad.

    Tagasta list sõnastikest kujul:
    {
        "user_id": ...,
        "full_name": ...,
        "username": ...,
        "email": ...,
        "city": ...,
        "company_name": ...
    }

    TODO:
    1. Tee requests.get(API_URL, timeout=30).
    2. Kutsu välja response.raise_for_status().
    3. Võta response.json() tulemus muutujasse data.
    4. Tee list kasutajatest sobival kujul.
    """
    raise NotImplementedError("Tee fetch_api_users funktsioon valmis.")


def read_notification_preferences():
    """Extract: loe JSON failist teavituseelistused.

    Tagasta list sõnastikest kujul:
    {
        "email": ...,
        "newsletter_opt_in": ...,
        "preferred_channel": ...,
        "updated_at": ...
    }

    TODO:
    1. Ava PREFERENCES_PATH fail.
    2. Loe fail json.load abil sisse.
    3. Tagasta loetud list.
    """
    raise NotImplementedError("Tee read_notification_preferences funktsioon valmis.")


def load_api_users(conn, api_users):
    """Load: salvesta API toorandmed staging tabelisse."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE staging.api_users;")
        for user in api_users:
            cur.execute(
                """
                INSERT INTO staging.api_users (
                    user_id,
                    full_name,
                    username,
                    email,
                    city,
                    company_name,
                    loaded_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW());
                """,
                (
                    user["user_id"],
                    user["full_name"],
                    user["username"],
                    user["email"],
                    user["city"],
                    user["company_name"],
                ),
            )
    conn.commit()


def load_notification_preferences(conn, preferences):
    """Load: salvesta JSON allika andmed staging tabelisse."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE staging.notification_preferences;")
        for item in preferences:
            cur.execute(
                """
                INSERT INTO staging.notification_preferences (
                    email,
                    newsletter_opt_in,
                    preferred_channel,
                    updated_at,
                    loaded_at
                )
                VALUES (%s, %s, %s, %s, NOW());
                """,
                (
                    item["email"],
                    item["newsletter_opt_in"],
                    item["preferred_channel"],
                    item["updated_at"],
                ),
            )
    conn.commit()


def read_status_lookup(conn):
    """Extract: loe CSV failist stagingusse jõudnud staatuseandmed."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT email, account_status, source_system, updated_at
            FROM staging.user_status
            """
        )
        rows = cur.fetchall()

    lookup = {}
    for email, account_status, source_system, updated_at in rows:
        lookup[normalize_email(email)] = {
            "account_status": account_status,
            "source_system": source_system,
            "updated_at": updated_at,
        }
    return lookup


def build_preference_lookup(preferences):
    lookup = {}
    for item in preferences:
        lookup[normalize_email(item["email"])] = {
            "newsletter_opt_in": item["newsletter_opt_in"],
            "preferred_channel": item["preferred_channel"],
            "updated_at": item["updated_at"],
        }
    return lookup


def build_final_rows(api_users, status_lookup, preference_lookup):
    """Transform: ehita lõpptabeli read.

    TODO:
    1. Käi kõik API kasutajad läbi.
    2. Võta kasutaja e-post ja puhasta see normalize_email abil.
    3. Otsi selle järgi sobiv rida status_lookup ja preference_lookup sõnastikest.
    4. Tagasta list tuplestest järgmises järjekorras:
       (
           user_id,
           full_name,
           username,
           email,
           city,
           company_name,
           account_status,
           source_system,
           newsletter_opt_in,
           preferred_channel
       )
    Kui mõnes rikastavas allikas vastet ei ole, jäta selle välja väärtuseks None.
    """
    raise NotImplementedError("Tee build_final_rows funktsioon valmis.")


def load_final_rows(conn, final_rows):
    """Load: salvesta lõpptulemus analytics skeema tabelisse."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE analytics.user_profile;")
        for row in final_rows:
            cur.execute(
                """
                INSERT INTO analytics.user_profile (
                    user_id,
                    full_name,
                    username,
                    email,
                    city,
                    company_name,
                    account_status,
                    source_system,
                    newsletter_opt_in,
                    preferred_channel,
                    loaded_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());
                """,
                row,
            )
    conn.commit()


def main():
    conn = get_connection()
    try:
        print("ETL etapp 1/3: Extract")
        api_users = fetch_api_users()
        preferences = read_notification_preferences()
        status_lookup = read_status_lookup(conn)
        print(f"- API-st tuli {len(api_users)} kasutajat.")
        print(f"- JSON failist tuli {len(preferences)} teavituseelistust.")
        print(f"- Staging-tabelist tuli {len(status_lookup)} staatusekirjet.")

        print("ETL etapp 2/3: Transform")
        preference_lookup = build_preference_lookup(preferences)
        final_rows = build_final_rows(api_users, status_lookup, preference_lookup)
        print(
            f"- Puhastasin e-posti ja ühendasin andmed {len(final_rows)} "
            "kasutaja jaoks."
        )

        print("ETL etapp 3/3: Load")
        load_api_users(conn, api_users)
        print(f"- Laadisin staging.api_users tabelisse {len(api_users)} rida.")
        load_notification_preferences(conn, preferences)
        print(
            "- Laadisin staging.notification_preferences tabelisse "
            f"{len(preferences)} rida."
        )
        load_final_rows(conn, final_rows)
        print(
            f"- Laadisin analytics.user_profile tabelisse {len(final_rows)} rida."
        )
        print("Valmis.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
