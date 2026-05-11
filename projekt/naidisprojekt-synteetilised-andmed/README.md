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
| Näidikulaud | Apache Superset 6.x | 3 interaktiivset chart'i |

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

# 2. Genereeri turvaline SECRET_KEY Superseti jaoks
#    Asenda .env failis SUPERSET_SECRET_KEY väärtus:
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Käivita kõik teenused
docker compose up -d --build

# 4. Oota ~2–3 minutit
docker compose ps   # kõik peaksid olema "running"

# 5. Käivita Airflow UI-s DAG käsitsi esimesel korral
#    http://localhost:8080  (kasutaja: airflow / parool: airflow)
#    → myyk_pipeline → "Trigger DAG"
#    DAG genereerib 90 päeva sünteetilised andmed ja käivitab dbt.

# 6. Superset: http://localhost:8088 (kasutaja: vt .env SUPERSET_ADMIN_USER/PASSWORD)
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

- `marts` → `mart_pood_paevane`
- `marts` → `mart_parimad_tunnid`

### 3. Loo chart'id

Dashboard koosneb 3 chart'ist:

| Chart | Tüüp | Dataset | Mõõdik / veerg |
|-------|------|---------|----------------|
| Kaupluste paremusjärjestus | Bar chart | `mart_pood_paevane` | X: `pood_nimi`, Y: `kesk_tohusus` (Average) |
| Kellaajamustrid | Line chart | `mart_parimad_tunnid` | X: `mootmise_tund`, Y: `kesk_tohusus` (Average), Series: `pood_nimi` |
| KPI — kõrgeim tõhusus | Big Number | `mart_pood_paevane` | Mõõdik: `max_tohusus` (MAX) |

**Charts → + Chart** → vali dataset ja chart tüüp → seadista → Save.

### 4. Loo dashboard

**Dashboards → + Dashboard** → anna nimi (nt "EstiMüük OÜ — müügitõhusus") → lohista chart'id paika → Publish.

### 5. Ekspordi dashboard (ZIP reposse)

```bash
# Ekspordi loodud dashboard ZIP-failina
docker compose exec superset superset export-dashboards \
  -f /app/dashboards/myyk_dashboard.zip

# Kopeeri ZIP hosti failisüsteemi
docker compose cp superset:/app/dashboards/myyk_dashboard.zip \
  superset/dashboards/myyk_dashboard.zip

# Nüüd saab ZIP-i reposse commitida
git add superset/dashboards/myyk_dashboard.zip
```

### 6. Impordi dashboard (kui ZIP on juba reposis)

```bash
bash scripts/import_dashboard.sh
```

Või käsitsi:
```bash
docker compose cp superset/dashboards/myyk_dashboard.zip \
  superset:/app/dashboards/myyk_dashboard.zip

docker compose exec superset superset import-dashboards \
  --path /app/dashboards/myyk_dashboard.zip \
  --username admin
```

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
