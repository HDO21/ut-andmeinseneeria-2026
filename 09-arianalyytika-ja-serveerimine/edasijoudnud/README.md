# Praktikum 9: Arianaluutika ja andmete serveerimine (Edasijoudnud)

## Eesmärk

Ehitada terviklik BI-lahendus: CSV andmed laaditakse pgduckdb andmebaasi, dbt teisendab need
analuutikakihtideks ja Apache Superset serveerib visualisatsioonid dashboardi kaudu.

## Oppivaljundid

- Seadistada Apache Superset ja uhendada see PostgreSQL andmebaasiga
- Kasutada SQL Lab-i andmete uurimiseks
- Registreerida andmestikud (dataset) ja ehitada graafikuid
- Koostada dashboard KPI-de esitlemiseks
- Moistab dbt staging → marts mustrit Superseti tarbeks

## Kausta struktuur

```
edasijoudnud/
├── compose.yml             # Koik teenused
├── .env.example            # Keskkonna muutujate mall
├── superset_config.py      # Superseti konfiguratsioon (SimpleCache, ilma Redisita)
├── Dockerfile.python
├── Dockerfile.dbt
├── data/                   # CSV andmefailid (supermarketi muugiandmed)
├── scripts/
│   ├── requirements.txt
│   └── 01_load_data.py     # Laeb CSV → raw skeem
└── dbt_project/
    ├── models/
    │   ├── staging/        # Vaated raw andmete pealt
    │   └── marts/          # Agregeeritud tabelid Superseti jaoks
    └── ...
```

---

## Ülesanne 0: Keskkonna ettevalmistamine

### 0.1 Kopeeri .env

```bash
cp .env.example .env
```

Muuda `.env` failis:
- `POSTGRES_PASSWORD` — vali oma parool
- `SUPERSET_DB_PASSWORD` — vali oma parool
- `SUPERSET_SECRET_KEY` — genereeri juhuslik string:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

### 0.2 Kaivita teenused

```bash
docker compose up -d
```

`superset-init` konteiner joob uks kord laabi (migratsioonid + admin kasutaja loomine).
See votab umbes 1-2 minutit. Kontrollimiseks:

```bash
docker compose logs superset-init
```

Superset on valmis kui `superset-init` on lopetanud ja `superset` konteiner joob.
Ava brauser: **http://localhost:8088** — logi sisse admin / admin (voi .env-s seadistatud parool).

---

## Ülesanne 1: Andmete laadimine

### 1.1 Laadi CSV failid andmebaasi

```bash
docker compose exec python python 01_load_data.py
```

Skript loob `raw` skeemi ja laeb sinna 7 tabelit (dim_date, dim_store, dim_product,
dim_supplier, dim_customer, dim_payment, fact_sales).

Kontrolli tulemus:

```bash
docker compose exec python python -c "
import psycopg2, os
conn = psycopg2.connect(host='db', dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'])
cur = conn.cursor()
for t in ['dim_date','dim_store','dim_product','fact_sales']:
    cur.execute(f'SELECT count(*) FROM raw.{t}')
    print(t, cur.fetchone()[0])
"
```

### 1.2 Joosta dbt mudelid

```bash
docker compose exec dbt dbt run
```

dbt loob kaks skeemikihti:
- `staging` — puhtad vaated raw andmete pealt
- `marts` — agregeeritud tabelid Superseti jaoks:
  - `mart_myyk_kuus` — igakuine muuk
  - `mart_myyk_kategooria` — muuk kategooria ja kuu loikes
  - `mart_myyk_piirkond` — muuk piirkonna ja kuu loikes

---

## Ülesanne 2: Superset — andmeuhenduse loomine

1. Mine **Settings → Database Connections → + Database**
2. Vali andmebaasi tyyp: **PostgreSQL**
3. Taidetud andmed:
   - Host: `db`
   - Port: `5432`
   - Database name: vaarumine .env-st (`POSTGRES_DB`)
   - Username / Password: .env-st (`POSTGRES_USER` / `POSTGRES_PASSWORD`)
4. Kliki **Test Connection** — peaks naitama "Connection looks good!"
5. Salvesta nimega **Praktikum DB**

---

## Ülesanne 3: SQL Lab

Mine **SQL → SQL Lab** ja provi:

```sql
-- Koik kategooriad ja nende kogutulu
SELECT category, SUM(tulu_kokku) AS tulu
FROM marts.mart_myyk_kategooria
GROUP BY category
ORDER BY tulu DESC;
```

```sql
-- Igakuine muuk trendina
SELECT month_start, tulu_kokku
FROM marts.mart_myyk_kuus
ORDER BY month_start;
```

```sql
-- Top 5 piirkond kogutulu jargi
SELECT region, SUM(tulu_kokku) AS tulu
FROM marts.mart_myyk_piirkond
GROUP BY region
ORDER BY tulu DESC
LIMIT 5;
```

---

## Ülesanne 4: Andmestike registreerimine

Mine **Datasets → + Dataset** ja registreeri:

| Dataset nimi | Schema | Tabel |
|---|---|---|
| Muuk kuus | marts | mart_myyk_kuus |
| Muuk kategooria jargi | marts | mart_myyk_kategooria |
| Muuk piirkonna jargi | marts | mart_myyk_piirkond |

---

## Ülesanne 5: Graafikute loomine

### 5.1 Igakuine muuk (joongraafik)

- Dataset: **Muuk kuus**
- Visualisation type: **Line Chart**
- X-axis: `month_start`
- Metrics: `SUM(tulu_kokku)`
- Salvesta nimega: **Igakuine muuk**

### 5.2 Muuk kategooria jargi (tulpdiagramm)

- Dataset: **Muuk kategooria jargi**
- Visualisation type: **Bar Chart**
- X-axis: `month_start`
- Metrics: `SUM(tulu_kokku)`
- Dimensions: `category`
- Salvesta nimega: **Muuk kategooria jargi**

### 5.3 KPI — kogutulu (suur number)

- Dataset: **Muuk kuus**
- Visualisation type: **Big Number with Trendline**
- Metric: `SUM(tulu_kokku)`
- Salvesta nimega: **Kogutulu KPI**

### 5.4 Piirkondade kaart (tulpdiagramm)

- Dataset: **Muuk piirkonna jargi**
- Visualisation type: **Bar Chart**
- X-axis: `region`
- Metrics: `SUM(tulu_kokku)`
- Salvesta nimega: **Muuk piirkondade kaupa**

---

## Ülesanne 6: Dashboard

1. Mine **Dashboards → + Dashboard**
2. Nimi: **Supermarketi Ullevaade**
3. Lisa graafikud:
   - Kogutulu KPI
   - Igakuine muuk
   - Muuk kategooria jargi
   - Muuk piirkondade kaupa
4. Paiguta graafikud loogiliselt (KPI-d üleval, detailid all)
5. Lisa filter: **Date Range** → `month_start` veerg
6. Salvesta ja avalda (**Publish**)

---

## Lisaülesanne: Mõõdiku definitsioon

Vali uks kolmest mart-mudelist ja kirjuta **mõõdiku definitsioon** — dokument mis vastab:

1. **Mis see mõõdik mõõdab?** (äriline tähendus)
2. **Kuidas arvutatakse?** (valem + filtrid)
3. **Millised on piirangud?** (mida see EI mõõda)
4. **Milline on granularity?** (kuu? päev? pood?)

---

## Uued mõisted

| Mõiste | Selgitus |
|--------|----------|
| **Superset** | Apache Superset — avatud lähtekoodiga BI ja visualiseerimise platvorm |
| **Dataset** | Superseti andmestiku registreering — osutab SQL-tabelile voi vaatele |
| **SQL Lab** | Superseti interaktiivne SQL editor |
| **Slice** | Superset-is graafiku nimetus (chart = slice) |
| **SimpleCache** | Mälupõhine vahemälu, mis ei vaja Redis-t |
| **Marts** | dbt-s lõppkasutajale mõeldud koondtabelid |

## Viited

- [Apache Superset dokumentatsioon](https://superset.apache.org/docs/intro)
- [Superset SQL Lab](https://superset.apache.org/docs/using-superset/exploring-data)
- [dbt staging/marts muster](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
