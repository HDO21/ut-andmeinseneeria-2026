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
| Näidikulaud | Apache Superset 6.x | 3 interaktiivset chart'i |
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

# 2. Genereeri turvaline SECRET_KEY Superseti jaoks
#    Asenda .env failis SUPERSET_SECRET_KEY väärtus:
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Käivita kõik teenused
docker compose up -d --build

# 4. Oota ~2–3 minutit, kuni Superset initsialiseerub
docker compose ps   # kõik peaksid olema "running" või "healthy"

# 5. Ava Airflow UI ja käivita DAG käsitsi esimesel korral
#    http://localhost:8080  (kasutaja: airflow / parool: airflow)
#    → ilmaandmed_pipeline → "Trigger DAG" nupp

# 6. Ava Superset ja loo ühendus andmebaasiga
#    http://localhost:8088  (kasutaja: vt .env SUPERSET_ADMIN_USER/PASSWORD)
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

## Superset seadistus

Kui `docker compose up` on käivitunud ja DAG vähemalt korra edukalt läbi jooksnud, järgi neid samme:

### 1. Loo andmebaasi ühendus

Ava **http://localhost:8088** → logi sisse (vt `.env` `SUPERSET_ADMIN_USER/PASSWORD`).

**Settings → Database Connections → + Database → PostgreSQL**

| Väli | Väärtus |
|------|---------|
| HOST | `analytics-db` |
| PORT | `5432` |
| DATABASE NAME | `praktikum` |
| USERNAME | `praktikum` |
| PASSWORD | `praktikum` |

Või lisa SQLAlchemy URI otse:
```
postgresql+psycopg2://praktikum:praktikum@analytics-db:5432/praktikum
```

### 2. Registreeri datasetid

**Datasets → + Dataset** — vali loodud ühendus ja registreeri kaks tabelit:

- `marts` → `mart_paeva_kokkuvote`
- `marts` → `mart_parimad_ajavahemikud`

### 3. Loo chart'id

Dashboard koosneb 3 chart'ist:

| Chart | Tüüp | Dataset | Mõõdik / veerg |
|-------|------|---------|----------------|
| Linnade paremusjärjestus | Bar chart | `mart_paeva_kokkuvote` | X: `asukoha_nimi`, Y: `kesk_skoor` (Average) |
| Parimad ajaaknad | Table | `mart_parimad_ajavahemikud` | Veerud: `asukoha_nimi`, `vahemiku_algus`, `kesk_skoor`, `soovitus` |
| Päevane KPI | Big Number | `mart_paeva_kokkuvote` | Mõõdik: `max_skoor` (MAX) |

**Charts → + Chart** → vali dataset ja chart tüüp → seadista → Save.

### 4. Loo dashboard

**Dashboards → + Dashboard** → anna nimi (nt "Ilmaandmed — välitegevuse sobivus") → lohista chart'id paika → Publish.

### 5. Ekspordi dashboard (ZIP reposse)

```bash
# Ekspordi loodud dashboard ZIP-failina
docker compose exec superset superset export-dashboards \
  -f /app/dashboards/ilmaandmed_dashboard.zip

# Kopeeri ZIP hosti failisüsteemi
docker compose cp superset:/app/dashboards/ilmaandmed_dashboard.zip \
  superset/dashboards/ilmaandmed_dashboard.zip

# Nüüd saab ZIP-i reposse commitida
git add superset/dashboards/ilmaandmed_dashboard.zip
```

### 6. Impordi dashboard (kui ZIP on juba reposis)

```bash
bash scripts/import_dashboard.sh
```

Või käsitsi:
```bash
docker compose cp superset/dashboards/ilmaandmed_dashboard.zip \
  superset:/app/dashboards/ilmaandmed_dashboard.zip

docker compose exec superset superset import-dashboards \
  --path /app/dashboards/ilmaandmed_dashboard.zip \
  --username admin
```

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
