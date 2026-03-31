"""Kommenteeritud näide kahe allika ETL töövoost.

Selle faili eesmärk ei ole ainult töö ära teha, vaid aidata lugeda Pythoni
koodi samm-sammult. Kui Python on sulle veel uus, siis loe kommentaare rahulikult
ülevalt alla.

Fail teeb järgmise töö:

Extract:
- loeb kasutajad API-st
- loeb kasutajastaatused staging.user_status tabelist

Transform:
- puhastab e-posti aadressi
- ühendab API ja CSV allika andmed ühe võtme alusel

Load:
- salvestab API toorandmed staging.api_users tabelisse
- salvestab lõpptulemuse analytics.user_profile tabelisse
"""

# import toob faili sisse teegid, mida me allpool kasutame
import os

import psycopg2
import requests


# Kuidas lugeda funktsiooni päist?
#
# def funktsiooni_nimi(arg1, arg2):
#     ...
#
# def = alustame uue funktsiooni kirjeldamist
# funktsiooni_nimi = nimi, millega saame seda funktsiooni hiljem välja kutsuda
# arg1, arg2 = sisendid ehk argumendid, mille funktsioon käivitamisel kaasa saab
# : kooloni järel algab funktsiooni keha ehk sisse taandatud koodiplokk
#
# Näide:
# normalize_email(value)
# tähendab, et funktsioon saab ühe sisendi nimega value.
# Kui me kutsume selle välja kujul normalize_email(user["email"]),
# siis value hakkab funktsiooni sees tähendama user["email"] väärtust.


# Muutujad, mis kirjutatakse suurte tähtedega, on tavaliselt "konstandid":
# väärtused, mida me ei plaani programmi töö jooksul muuta.
API_URL = "https://jsonplaceholder.typicode.com/users"


def get_connection():
    """Loo andmebaasiühendus.

    def tähendab funktsiooni definitsiooni.
    return annab funktsiooni tulemuse välja.

    Siin kasutame keskkonnamuutujaid. See tähendab, et kasutajanimi,
    parool ja muud ühenduse väärtused ei ole kõvasti koodi sisse kirjutatud.
    """

    # psycopg2.connect on funktsioon teegist psycopg2, mille importisime üleval.
    # Selle funktsiooni tagastusväärtus on connection objekt.
    # Hiljem paneme selle conn muutujasse:
    # conn = get_connection()
    #
    # See tähendab, et conn "päritolu" on:
    # get_connection -> psycopg2.connect -> connection objekt
    return psycopg2.connect(
        # os.environ.get("NIMI", "vaikimisi") küsib väärtust keskkonnast.
        # Kui väärtust ei ole, kasutatakse parempoolset vaikimisi varianti.
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "praktikum"),
        password=os.environ.get("DB_PASSWORD", "praktikum"),
        dbname=os.environ.get("DB_NAME", "praktikum"),
    )


def normalize_email(value):
    """Transform: puhasta e-post ühendamiseks sobivaks.

    See funktsioon näitab väikest, aga väga levinud Pythoni mustrit:
    kontrollime kõigepealt erijuhtu ja siis tagastame puhastatud väärtuse.

    Siin on value lihtsalt kohatäide sisendi jaoks.
    Selle funktsiooni eri väljakutsetes võib value tulla eri kohtadest:
    - normalize_email(user["email"]) -> value tuleb API kasutaja kirjest
    - normalize_email(email) -> value tuleb andmebaasist loetud reast
    """

    # None tähendab siin "väärtus puudub".
    if value is None:
        return None

    # strip eemaldab tühikud algusest ja lõpust
    # lower muudab teksti väikesteks tähtedeks
    return value.strip().lower()


def fetch_api_users():
    """Extract: loe kasutajad API-st.

    Funktsioon tagastab listi sõnastikest.
    List = mitme elemendi järjestatud kogu
    Sõnastik = võtme-väärtuse paarid, näiteks {"email": "..."}
    """

    # requests.get on funktsioon teegist requests.
    # See tagastab Response objekti, mille paneme muutujasse response.
    #
    # Muutuja päritolu on siin:
    # requests.get(...) -> Response objekt -> response
    response = requests.get(API_URL, timeout=30)

    # raise_for_status EI ole meie enda funktsioon selles failis.
    # See on requests Response objekti meetod.
    # Meetod tähendab sisuliselt funktsiooni, mis kuulub mingi objekti juurde.
    #
    # Kuna response on Response objekt, saame kasutada selle meetodeid:
    # response.raise_for_status()
    # response.json()
    response.raise_for_status()

    # json() muudab API vastuse Pythoni andmestruktuuriks
    # Siin on tulemuseks list, mille iga element on üks kasutaja.
    # Ka json() on samuti Response objekti meetod.
    data = response.json()

    # Loome tühja listi, kuhu hakkame kasutajate puhastatud kujusid lisama.
    users = []

    # for kordab sama tegevust iga elemendi jaoks.
    # item on iga kasutaja andmeid sisaldav sõnastik.
    for item in data:
        # append lisab listi lõppu ühe uue elemendi.
        users.append(
            {
                # Vasakul on meie enda valitud võtmenimi.
                # Paremal on väärtus API vastusest.
                "user_id": item["id"],
                # " ".join(...) ühendab listi elemendid üheks tekstiks.
                # split() jagab teksti sõnadeks. Koos aitavad need eemaldada
                # liigsed topelttühikud.
                "full_name": " ".join(item["name"].split()),
                "username": item["username"],
                "email": item["email"],
                # API andmed võivad olla pesastatud.
                # item["address"]["city"] tähendab:
                # võta kõigepealt address ja siis selle seest city.
                "city": item["address"]["city"],
                "company_name": item["company"]["name"],
            }
        )

    return users


def load_api_users(conn, api_users):
    """Load: salvesta API toorandmed staging tabelisse."""

    # Siin saab funktsioon kaks sisendit:
    # conn = andmebaasiühendus, mis loodi main() funktsioonis
    # api_users = list, mille tagastas fetch_api_users()

    # with ... as ... on kontekstihaldur.
    # See aitab ressursi korrektselt sulgeda, kui plokk lõppeb.
    #
    # conn on connection objekt.
    # conn.cursor() on selle objekti meetod, mis tagastab cursor objekti.
    # Paneme selle cursor objekti muutujasse cur.
    with conn.cursor() as cur:
        # TRUNCATE tühjendab tabeli kiiresti.
        # execute() on cursor objekti meetod.
        # Seega cur.execute(...) tähendab:
        # "käivita see SQL käsk selle kursori kaudu".
        cur.execute("TRUNCATE TABLE staging.api_users;")

        # Sama muster nagu enne: käime listi elemendid ükshaaval läbi.
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
                    # See tuppel peab olema samas järjekorras,
                    # nagu SQL VALUES osas olevad %s kohad.
                    user["user_id"],
                    user["full_name"],
                    user["username"],
                    user["email"],
                    user["city"],
                    user["company_name"],
                ),
            )

    # commit() on connection objekti meetod.
    # conn.commit() kinnitab andmebaasimuudatused.
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

        # fetchall tagastab kõik read listina.
        # Iga rida on tuppel.
        rows = cur.fetchall()

    # lookup tähendab siin abisõnastikku, kust saab väärtuse kiiresti kätte.
    lookup = {}

    # Siin kasutame Pythoni "lahtipakkimist":
    # iga rea neli välja võetakse kohe nelja muutujasse.
    #
    # Muutujate päritolu on siin:
    # conn -> cur -> cur.fetchall() -> rows -> üksikrida -> email, account_status, ...
    for email, account_status, source_system, updated_at in rows:
        lookup[normalize_email(email)] = {
            "account_status": account_status,
            "source_system": source_system,
            "updated_at": updated_at,
        }

    return lookup


def build_final_rows(api_users, status_lookup):
    """Transform: puhasta ühendusvõti ja ühenda API ning CSV andmed."""

    # api_users tuli funktsioonist fetch_api_users()
    # status_lookup tuli funktsioonist read_status_lookup()
    #
    # See on hea näide muutujate "lineage'ist" ehk päritolust:
    # fetch_api_users() -> api_users
    # read_status_lookup(conn) -> status_lookup
    # build_final_rows(api_users, status_lookup) -> final_rows
    rows = []

    for user in api_users:
        # Loome puhastatud võtme, mille järgi eri allikaid ühendada.
        email_key = normalize_email(user["email"])

        # dict.get võtab sõnastikust väärtuse.
        # Kui võtit ei leita, tagastab see None.
        # get() on sõnastiku ehk dict tüübi meetod.
        status = status_lookup.get(email_key)

        rows.append(
            (
                user["user_id"],
                user["full_name"],
                user["username"],
                email_key,
                user["city"],
                user["company_name"],
                # Tingimusavaldis "A if tingimus else B" on lühike viis öelda:
                # kui status on olemas, võta välja väärtus;
                # muidu pane None.
                status["account_status"] if status else None,
                status["source_system"] if status else None,
            )
        )

    return rows


def load_final_rows(conn, final_rows):
    """Load: salvesta lõpptulemus analytics skeema tabelisse."""

    # final_rows tuli funktsioonist build_final_rows(...)
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE analytics.user_profile;")

        for row in final_rows:
            # row on tuppel, mis pandi kokku build_final_rows funktsioonis.
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
                    loaded_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
                """,
                row,
            )

    conn.commit()


def main():
    """Programmi põhitöövoog.

    See funktsioon käivitab kõik eelnevad sammud õiges järjekorras.
    """

    conn = get_connection()

    # Siin algab kogu skripti põhiline muutujate teekond:
    # get_connection() -> conn
    # fetch_api_users() -> api_users
    # read_status_lookup(conn) -> status_lookup
    # build_final_rows(api_users, status_lookup) -> final_rows
    # load_api_users(conn, api_users) ja load_final_rows(conn, final_rows)
    # kasutavad eelnevate sammude tulemusi

    # try/finally tähendab:
    # proovi töö ära teha;
    # lõpuks sule ühendus igal juhul, isegi siis, kui kuskil tuleb viga.
    try:
        print("ETL etapp 1/3: Extract")

        # Kutsume välja varem defineeritud funktsioonid.
        api_users = fetch_api_users()
        status_lookup = read_status_lookup(conn)

        # f-string võimaldab muutujate väärtusi otse teksti sisse panna.
        print(f"- API-st tuli {len(api_users)} kasutajat.")
        print(f"- Staging-tabelist tuli {len(status_lookup)} staatusekirjet.")

        print("ETL etapp 2/3: Transform")
        final_rows = build_final_rows(api_users, status_lookup)
        print(
            f"- Puhastasin e-posti ja ühendasin andmed {len(final_rows)} "
            "kasutaja jaoks."
        )

        print("ETL etapp 3/3: Load")
        load_api_users(conn, api_users)
        print(f"- Laadisin staging.api_users tabelisse {len(api_users)} rida.")

        load_final_rows(conn, final_rows)
        print(
            f"- Laadisin analytics.user_profile tabelisse {len(final_rows)} rida."
        )
        print("Valmis.")
    finally:
        conn.close()


# See on väga levinud Pythoni muster.
# Kood selle if ploki sees käivitub siis, kui fail pannakse otse jooksma.
# Kui sama faili mõnest teisest failist importida, siis main() automaatselt ei käivitu.
if __name__ == "__main__":
    main()
