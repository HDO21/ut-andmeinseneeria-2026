# Praktikum 9: Ärianalüütika ja andmete serveerimine (Edasijõudnud)

## Eesmärk

Ehitada esitlusvalmis BI-lahendus: CSV-andmed laaditakse pgduckdb andmebaasi, dbt
teisendab need analüütikakihtideks ning Apache Superset serveerib visualisatsioonid
näidikulaua (Dashboard) kaudu. Praktikumi lõpus seostame mõõdikud nende ärilise tähenduse,
andmekvaliteedi ja arvutusmetoodikaga.

## Õpiväljundid

Praktikumi lõpuks osaleja:

- Seadistab Apache Superseti ja ühendab selle PostgreSQL andmebaasiga
- Kasutab SQL Labi andmete uurimiseks ja päringute katsetamiseks
- Registreerib andmekogumeid (Dataset) ning ehitab diagramme
- Koostab näidikulaua KPI-de esitlemiseks
- Mõistab dbt staging → marts mustrit analüütikavahendite tarbeks
- Oskab kirjutada mõõdiku definitsiooni: valem, filtrid, piirangud ja detailsusaste

## Kausta struktuur

```
edasijoudnud/
├── compose.yml             # Kõik teenused
├── .env.example            # Keskkonnamuutujate mall
├── superset_config.py      # Superseti seadistus (SimpleCache, ilma Redisita)
├── Dockerfile.python
├── Dockerfile.dbt
├── data/                   # CSV-andmefailid (supermarketi müügiandmed)
├── scripts/
│   ├── requirements.txt
│   └── 01_load_data.py     # Laeb CSV → raw-skeem
└── dbt_project/
    ├── macros/
    │   └── generate_schema_name.sql  # Kohandab skeemi nimetamist
    ├── models/
    │   ├── staging/        # Vaated raw-andmete pealt
    │   └── marts/          # Koondtabelid Superseti jaoks
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

### 0.2 Käivita teenused

```bash
docker compose up -d
```

`superset-init` konteiner jookseb üks kord läbi (migratsioonid + administraatori
kasutaja loomine). See võtab umbes 1–2 minutit. Kontrollimiseks:

```bash
docker compose logs superset-init
```

Superset on valmis, kui `superset-init` on lõpetanud ja `superset` konteiner
jookseb. Ava brauser: **http://localhost:8088** — logi sisse `.env`-s seadistatud
kasutajanime ja parooliga (vaikimisi `admin` / `admin`).

---

## Ülesanne 1: Andmete laadimine

### 1.1 Laadi CSV-failid andmebaasi

```bash
docker compose exec python python 01_load_data.py
```

Skript loob `raw`-skeemi ja laeb sinna 7 tabelit:
`dim_date`, `dim_store`, `dim_product`, `dim_supplier`, `dim_customer`, `dim_payment`, `fact_sales`.

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

### 1.2 Käivita dbt mudelid

```bash
docker compose exec dbt dbt run
```

dbt loob kaks skeemikihti:
- `staging` — puhtad vaated raw-andmete pealt
- `marts` — koondtabelid Superseti jaoks:
  - `mart_myyk_kuus` — igakuine müük
  - `mart_myyk_kategooria` — müük tootekategooria ja kuu lõikes
  - `mart_myyk_piirkond` — müük piirkonna ja kuu lõikes

---

## Ülesanne 2: Superset — andmeühenduse loomine

1. Mine **Settings → Database Connections → + Database**
2. Vali andmebaasi tüüp: **PostgreSQL**
3. Täida ühenduse andmed:
   - Host: `db`
   - Port: `5432`
   - Database name: väärtus `.env`-st (`POSTGRES_DB`)
   - Username / Password: väärtused `.env`-st (`POSTGRES_USER` / `POSTGRES_PASSWORD`)
4. Klõpsa **Test Connection** — peaks näitama „Connection looks good!"
5. Salvesta nimega **Praktikum DB**

---

## Ülesanne 3: SQL Lab

Mine **SQL → SQL Lab** ja proovi:

```sql
-- Kõik kategooriad ja nende kogutulu
SELECT category, SUM(tulu_kokku) AS tulu
FROM marts.mart_myyk_kategooria
GROUP BY category
ORDER BY tulu DESC;
```

```sql
-- Igakuine müük trendina
SELECT month_start, tulu_kokku
FROM marts.mart_myyk_kuus
ORDER BY month_start;
```

```sql
-- Top 5 piirkonda kogutulu järgi
SELECT region, SUM(tulu_kokku) AS tulu
FROM marts.mart_myyk_piirkond
GROUP BY region
ORDER BY tulu DESC
LIMIT 5;
```

---

## Ülesanne 4: Andmekogumite registreerimine

Mine **Datasets → + Dataset** ja registreeri:

| Andmekogumi nimi | Skeem | Tabel |
|---|---|---|
| Müük kuus | marts | mart_myyk_kuus |
| Müük kategooria järgi | marts | mart_myyk_kategooria |
| Müük piirkonna järgi | marts | mart_myyk_piirkond |

---

## Ülesanne 5: Diagrammide loomine

### 5.1 Igakuine müük (joondiagramm)

- Dataset: **Müük kuus**
- Visualization type: **Line Chart**
- X-axis: `month_start`
- Metrics: `SUM(tulu_kokku)`
- Salvesta nimega: **Igakuine müük**

### 5.2 Müük kategooriate kaupa (tulpdiagramm)

- Dataset: **Müük kategooria järgi**
- Visualization type: **Bar Chart**
- X-axis: `month_start`
- Metrics: `SUM(tulu_kokku)`
- Dimensions: `category`
- Salvesta nimega: **Müük kategooriate kaupa**

### 5.3 KPI — kogutulu (suur arv)

- Dataset: **Müük kuus**
- Visualization type: **Big Number with Trendline**
- Metric: `SUM(tulu_kokku)`
- Salvesta nimega: **Kogutulu KPI**

### 5.4 Müük piirkondade kaupa (tulpdiagramm)

- Dataset: **Müük piirkonna järgi**
- Visualization type: **Bar Chart**
- X-axis: `region`
- Metrics: `SUM(tulu_kokku)`
- Salvesta nimega: **Müük piirkondade kaupa**

---

## Ülesanne 6: Näidikulaud

1. Mine **Dashboards → + Dashboard**
2. Nimi: **Supermarketi ülevaade**
3. Lisa diagrammid:
   - Kogutulu KPI
   - Igakuine müük
   - Müük kategooriate kaupa
   - Müük piirkondade kaupa
4. Paiguta diagrammid loogiliselt (KPI-d ülaosas, detailid all)
5. Lisa filter: **Date Range** → veerg `month_start`
6. Salvesta ja avalda (**Publish**)

---

## Lisaülesanne: Mõõdiku definitsioon

Vali üks kolmest mart-mudelist ja kirjuta **mõõdiku definitsioon** — dokument, mis vastab järgmistele küsimustele:

1. **Mida see mõõdik mõõdab?** (äriline tähendus)
2. **Kuidas arvutatakse?** (valem + filtrid)
3. **Millised on piirangud?** (mida see EI mõõda)
4. **Milline on detailsusaste?** (_granularity_ — kuu? päev? pood?)

---

## Uued mõisted

| Mõiste | Selgitus |
|--------|----------|
| **Apache Superset** | Avatud lähtekoodiga BI- ja visualiseerimisplatvorm |
| **Andmekogum** (_Dataset_) | Superseti registreering, mis osutab SQL-tabelile või -vaatele |
| **SQL Lab** | Superseti interaktiivne SQL-redaktor |
| **Näidikulaud** (_Dashboard_) | Diagrammide ja KPI-de koondvaade |
| **Vahemälu** (_Cache_) | Puhvermälu, kuhu salvestatakse korduvpäringute tulemused kiirema juurdepääsu tagamiseks |
| **Mart** | dbt-s lõppkasutajale mõeldud koondtabel |
| **Detailsusaste** (_granularity_) | Andmerea täpsustase — nt üks rida kuu, kaupluse ja kategooria kohta |

## Viited

- [Apache Superset dokumentatsioon](https://superset.apache.org/docs/intro)
- [Superset SQL Lab](https://superset.apache.org/docs/using-superset/exploring-data)
- [dbt staging/marts muster](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- [Eesti IT-sõnastik (AKIT)](http://akit.cyber.ee)
