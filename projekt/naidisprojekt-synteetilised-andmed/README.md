# Näidisprojekt: Sünteetilised andmed — EstiMüük OÜ müügitõhusus

See näidisprojekt on mõeldud gruppidele, kes soovivad analüüsida **tööandja äriprobleemi**,
kuid ei saa tundlikke andmeid avaliku repoga jagada. Näide näitab, kuidas luua
statistiliselt usaldusväärne sünteetiline andmestik ja ehitada selle peale täielik pipeline.

## Stsenaarium

> **EstiMüük OÜ** on kaheksa kauplusega fiktiivsete kaupluste kett. Ärianalüütika tiim
> soovib mõista, millistes kauplustes ja mis kellaaegadel on müügitõhusus kõrgeim, et
> optimeerida personaligraafikuid ja reklaamikulutusi.
>
> Pärisandmed sisaldavad klientide isikuteavet ja konfidentsiaalset hinnainfot, mida
> ei saa avaliku repoga jagada. Seetõttu lõi tiim statistiliselt samaväärse
> **sünteetilise andmestiku** (`scripts/generate_data.py`), mis jäljendab pärisandmete
> struktuuri ja hooajalisi mustreid, kuid ei sisalda ühtegi päris tehingut ega klienti.

## Äriküsimus

Millistes kauplustes ja mis kellaaegadel on müügitõhusus (käive külastaja kohta) kõrgeim?

**Mõõdikud:**
1. Müügitõhusus (€/külaline) kaupluse ja kellaaja lõikes
2. Päevane käive ja külastatavus kaupluse kohta
3. Kellaaegade mustrid — hommik, lõuna, pärastlõuna

## Stack

| Komponent | Tööriist | Otstarve |
|-----------|---------|---------|
| Andmegeneraator | Python + numpy | Loob sünteetilised tunnipõhised müügiandmed |
| Orkestreerimine | Apache Airflow 3.x | Ajakavastab genereerimise ja dbt käivitamise |
| Transformatsioon | dbt Core 1.10 | Puhastab, arvutab tõhususe, koondab |
| Andmehoidla | PostgreSQL (pgDuckDB) | staging + intermediate + marts kihid |
| Näidikulaud | Apache Superset 4.x | 3 interaktiivset chart'i |

## Projekti struktuur

```
.
├── compose.yml                    ← kõik teenused
├── .env.example                   ← kopeeri .env-iks
├── .gitignore
├── scripts/
│   ├── generate_data.py           ← PEAMINE: sünteetiliste andmete generaator
│   └── import_dashboard.sh
├── airflow/
│   └── dags/
│       └── myygipipeline.py       ← Airflow DAG (generate → dbt run → dbt test)
├── dbt_project/
│   ├── seeds/
│   │   └── pood.csv               ← 8 fiktiivsed kauplused
│   ├── models/
│   │   ├── staging/               ← 1 mudel (stg_myygiandmed)
│   │   ├── intermediate/          ← 1 mudel (int_myyk_tunnipohine)
│   │   └── marts/                 ← 2 mudelit (pood_paevane, parimad_tunnid)
│   └── macros/
├── init/
│   └── 01_create_schemas.sql
├── superset/
│   ├── superset_config.py
│   └── dashboards/
└── docs/
    ├── arhitektuur.md
    └── progress.md
```

## Käivitamine

```bash
# 1. Kopeeri keskkonnamuutujad
cp .env.example .env

# 2. Käivita kõik teenused
docker compose up -d --build

# 3. Oota ~2–3 minutit
docker compose ps   # kõik peaksid olema "running"

# 4. Käivita Airflow UI-s DAG käsitsi esimesel korral
#    http://localhost:8080  (kasutaja: airflow / parool: airflow)
#    → myyk_pipeline → "Trigger DAG"
#    DAG genereerib 90 päeva sünteetilised andmed ja käivitab dbt.

# 5. Superset: http://localhost:8088 (kasutaja: admin / parool: admin)
#    Loo ühendus: Settings > Database Connections > + Database
#    URI: postgresql+psycopg2://praktikum:praktikum@analytics-db:5432/praktikum
```

## Sünteetiliste andmete generaator

`scripts/generate_data.py` loob 90 päeva müügiandmeid kaheksa kaupluse kohta.

**Kuidas mustrid töötavad:**
- Lahtiolekuajad: 8–22 tundi
- Lõunatipp (12–14h): 1,6–1,8× baasmaht
- Nädalavahetus: 1,3× baasmaht
- Juhuslik müra: ±20%

**Kohandamine oma projekti jaoks:**
```python
# Muuda KAUPLUSED nimekirja struktuur oma kaupluste/asukohtade järgi
# Muuda TUNNI_KORDAJAD oma äri rütmi järgi
# Muuda baas_kaive oma valdkonna keskmiste järgi
```

Generaator kasutab fikseeritud juhusliku generaatori seemet (`seed=42`), mis tagab
reprodutseeritavuse — sama seeme annab alati sama andmestiku.

## Superset dashboard

Dashboard koosneb 3 chart'ist:

| Chart | Tüüp | Andmed |
|-------|------|--------|
| Kaupluste paremusjärjestus | Bar chart | `mart_pood_paevane` — kesk_tohusus |
| Kellaajamustrid | Line chart | `mart_parimad_tunnid` — kesk_tohusus tunni lõikes |
| KPI paarik | Big Number | `mart_pood_paevane` — max tõhusus + kogukäive |

## Mida see näide NÄITAB

1. **Sünteetiliste andmete lähenemist** — miks, millal ja kuidas kasutada
2. **Generaatori läbipaistvust** — kõik mustrid on koodis nähtavad ja muudetavad
3. **Sama stacki** (Airflow + dbt + Superset) mis `naidisprojekt-ilmaandmed-dbt-ja-airflow`
4. **Idempotentset DAG'i** — korduvkäivitused ei kahekordista andmeid

## Oma projekti jaoks kohandamine

Asenda `KAUPLUSED` nimekirja oma andmeallikatega (töötajad, tooted, piirkonnad, jne).
Kohandada tuleb:
1. `scripts/generate_data.py` — muutujad ja mustrid
2. `seeds/pood.csv` → oma dimensioonitabel
3. `init/01_create_schemas.sql` → raw tabeli struktuur
4. `dbt_project/models/` → staging ja intermediate mudeli SQL

Rohkem infot: [`docs/arhitektuur.md`](docs/arhitektuur.md)
