# Näidisprojekt: Ilmaandmed — Airflow + dbt + Superset

See näidisprojekt lahendab sama äriküsimuse mis `naidisprojekt-ilmaandmed`, kuid kasutab
**edasijõudnute stacki**: Airflow orkestreerib töövoo, dbt teeb transformatsioonid, Superset näitab tulemusi.

> Lihtsamat varianti (Python + Streamlit + cron) vaata kaustast `../naidisprojekt-ilmaandmed`.

## Äriküsimus

Millistes Eesti asulates ja millistel järgmistel päevadel on ilm kõige sobivam välitegevuste, rattasõidu või õues toimuva ürituse planeerimiseks?

**Mõõdikud:**
1. Välitegevuse sobivuse skoor (0–100) iga tunni kohta
2. Parimad 3-tunnised ajaaknad (kesk_skoor ≥ 50) päeva ja asukoha lõikes
3. Päevane soovitus (Väga sobiv / Sobiv / Piiripealne / Ebasoodne)

## Stack

| Komponent | Tööriist | Otstarve |
|-----------|---------|---------|
| Orkestreerimine | Apache Airflow 3.x | Ajakavastab andmete laadimise ja dbt käivitamise |
| Transformatsioon | dbt Core 1.10 | Puhastab, skoorib ja koondab andmed |
| Andmehoidla | PostgreSQL (pgDuckDB) | staging + intermediate + marts kihid |
| Näidikulaud | Apache Superset 4.x | 3 interaktiivset chart'i |
| Andmeallikas | Open-Meteo API | Avalik, tasuta, ilma võtmeta |

## Andmevoog

```
Open-Meteo API
    ↓ (Airflow PythonOperator, @hourly)
staging.ilmaandmed_raw           ← toorandmed
    ↓ (dbt staging view)
staging.stg_ilmaandmed           ← puhastatud
    ↓ (dbt intermediate view)
intermediate.int_ilmaandmed_skoor ← tunnipõhine skoor
    ↓ (dbt marts tables)
marts.mart_paeva_kokkuvote       ← päevane kokkuvõte
marts.mart_parimad_ajavahemikud  ← parimad 3h aknad
    ↓
Superset dashboard
```

## Projekti struktuur

```
.
├── compose.yml                    ← kõik teenused
├── .env.example                   ← kopeeri .env-iks
├── .gitignore
├── airflow/
│   └── dags/
│       └── ilmaandmed_pipeline.py ← Airflow DAG (fetch → dbt run → dbt test)
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── seeds/
│   │   └── asukohad.csv           ← 10 Eesti linna koordinaatidega
│   ├── models/
│   │   ├── staging/               ← 1 mudel (stg_ilmaandmed)
│   │   ├── intermediate/          ← 1 mudel (int_ilmaandmed_skoor)
│   │   └── marts/                 ← 2 mudelit (paeva_kokkuvote, parimad_ajavahemikud)
│   └── macros/
│       └── generate_schema_name.sql
├── init/
│   └── 01_create_schemas.sql      ← loob staging skeemi ja toorandmete tabelid
├── superset/
│   ├── superset_config.py         ← Superset konfiguratsioon
│   └── dashboards/                ← dashboard eksportfailid (lisatakse pärast seadistust)
├── scripts/
│   └── import_dashboard.sh        ← dashboard importimise abiskript
└── docs/
    ├── arhitektuur.md             ← nädal 1 väljund
    └── progress.md                ← nädal 2 väljund
```

## Käivitamine

```bash
# 1. Kopeeri keskkonnamuutujad
cp .env.example .env

# 2. Käivita kõik teenused
docker compose up -d --build

# 3. Oota ~2–3 minutit, kuni Superset initsialiseerub
docker compose ps   # kõik peaksid olema "running" või "healthy"

# 4. Ava Airflow UI ja käivita DAG käsitsi esimesel korral
#    http://localhost:8080  (kasutaja: airflow / parool: airflow)
#    → ilmaandmed_pipeline → "Trigger DAG" nupp

# 5. Ava Superset ja loo ühendus andmebaasiga
#    http://localhost:8088  (kasutaja: admin / parool: admin)
#    Settings > Database Connections > + Database > PostgreSQL
#    SQLAlchemy URI: postgresql+psycopg2://praktikum:praktikum@analytics-db:5432/praktikum
```

Seejärel saab Supersetti luua chart'e otse `marts.*` tabelitest.

## dbt käsud (käsitsi käivitamiseks)

```bash
# Vaata Airflow konteineris (dbt on sealt kättesaadav):
docker compose exec airflow bash

# Projekti kaustas:
cd /opt/airflow/dbt_project

dbt seed --profiles-dir .        # laadib asukohad.csv
dbt run --profiles-dir .         # käivitab kõik mudelid
dbt test --profiles-dir .        # käivitab testid
dbt docs generate --profiles-dir .  # genereerib dokumentatsiooni
```

## Superset dashboard

Dashboard koosneb 3 chart'ist:

| Chart | Tüüp | Andmed |
|-------|------|--------|
| Linnade paremusjärjestus | Bar chart | `mart_paeva_kokkuvote` — kesk_skoor täna |
| Parimad ajaaknad | Table | `mart_parimad_ajavahemikud` — top 20 akent |
| Päevane KPI | Big Number | `mart_paeva_kokkuvote` — kõrgeim max_skoor |

Dashboard eksportimise ja importimise juhend: `scripts/import_dashboard.sh`

## Arhitektuur ja täpsemad otsused

Vaata: [`docs/arhitektuur.md`](docs/arhitektuur.md)

## Mida see näide NÄITAB vs mida EI NÄITA

**Näitab:**
- Airflow + dbt + Superset integreerimist ühes `compose.yml`-s
- Lihtsat DAG'i ilma keerukate mustriteta (PythonOperator + BashOperator)
- dbt staging → intermediate → marts kihide mõtet
- dbt testide kirjutamist (schema.yml)
- Superset'i liitmist andmebaasiga

**Ei näita** (hoitud lihtsana):
- Airflow TaskFlow API-d
- Airflow dynamic task mapping'ut
- dbt makrosid (v.a generate_schema_name)
- dbt snapshots / SCD2 pattern'i
- Superset'i kasutajate ja õiguste haldust
