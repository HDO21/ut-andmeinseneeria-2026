# Praktikum 9: Ärianalüütika ja andmete serveerimine (Edasijõudnud)

## Eesmärk

Ehitada esitlusvalmis BI-lahendus ja tutvuda andmete serveerimise erinevate viisidega.
CSV-andmed laaditakse pgduckdb andmebaasi, dbt teisendab need analüütikakihtideks,
Apache Superset serveerib visualisatsioonid näidikulaua kaudu ning FastAPI kaudu
tehakse sama andmekiht kättesaadavaks ka programmeeritavalt. Praktikumi lõpus
seostame mõõdikud nende ärilise tähenduse, andmekvaliteedi ja arvutusmetoodikaga.

---

## Andmete serveerimine: ülevaade

Enne harjutusi: miks on andmete serveerimine eraldi teema ja milliseid valikuid
andmeinsener igapäevaselt teeb.

### Kellele ja milleks?

Andmeid tarbitakse kolmel erineval viisil sõltuvalt tarbija rollist:

| Tarbija | Mida vajab | Tüüpiline lahendus |
|---------|------------|-------------------|
| **Inimene** (ärikasutaja, juht) | Visuaalne ülevaade, KPI-d | BI-tööriistad (Superset, Power BI, Tableau) |
| **Mudel** (ML-konveier) | Struktureeritud tunnusandmed, värskus | Feature store, API, andmeladu |
| **Operatiivne süsteem** (CRM, turundustööriist) | Töödeldud andmed tagasi allikasse | Reverse ETL (Census, Hightouch) |

### Serveerimisviisid: plussid ja miinused

| Viis | Kirjeldus | Plussid | Miinused | Sobib |
|------|-----------|---------|----------|-------|
| **SQL-juurdepääs** | Otse andmebaasi vastu SQL-päringuid | Paindlik; ligipääs tooresandmele | Nõuab SQL-oskust; halvad päringud aeglustavad DB-d | Analüütikud, andmeinsenerid |
| **BI / näidikulaud** | Visuaalvahendid (Superset, Power BI, Tableau) | Kasutajasõbralik; ühtlustatud mõõdikud | Näidikulaudade paljunemine; jäik uute küsimuste jaoks | Ärikasutajad, juhtkond |
| **Failieksport** | Perioodiline CSV/Excel/Parquet eksport | Universaalne; jagamine lihtne | Aegunud andmed; versioonikäos (`final_v2_revised.csv`) | Välispartnerid, ühekordsed raportid |
| **API pull** | Välissüsteemid pärivad andmeid REST API kaudu | Abstraheerib DB-d; täpsem juurdepääsukontroll | Arendustöö mahukas; struktuur on jäik | Rakendused, ML-teenused, partnerid |
| **API push (Reverse ETL)** | Konveier saadab andmeid välissüsteemide API-desse | Andmed jõuavad kasutatavatesse tööriistadesse; automatiseeritud | Sõltub välissüsteemist; keeruline siluda | SaaS-tööriistad (CRM, turundustööriistad) |
| **Sündmuste voog** | Reaalajas sündmuste edastus | Väga madal latentsus | Keerukas infrastruktuur | Reaalajarakendused (vt praktikum 8) |

> **Tähelepanekuid:**
> - SQL-juurdepääsu jõudlusriski leevendamiseks kasutatakse toodangus tihti **lugemisreplikat** (_read replica_), eraldi andmebaasi koopiat, mis võtab analüütikute päringukoormuse põhiandmebaasilt. See on aga pigem **ajutine lahendus enne pühendatud analüütika andmeplatvormi** (andmeladu, andmejärv) olemasolu. Kui analüütika andmebaas on OLTP-süsteemist eraldatud (nagu selles praktikumis), pole lugemisreplika vajalik, sest päringukoormuse eraldamine on lahendatud arhitektuuri tasemel.
> - „API pull on arendusmahukas" kehtib täielike toodangulahenduste kohta. Tänapäeval teeb FastAPI lihtsa sisemise API loomise oluliselt kiiremaks.
> - **Feature store** (nt Feast) on ML-maailmas omaette kategooria, mida tabelis eraldi ei kajastata, kuid mis on sisuliselt spetsialiseeritud API pull ML-tunnuste jaoks.

### Mida arvestada serveerimisel?

1. **Värskeoleku ja kiiruse tasakaal**: vaade on alati värske, kuid aeglasem; tabel on kiire, kuid aegunud; materiaalne vaade (_materialized view_) on kompromiss. dbt `marts` kasutab tabeleid, mis tagab kiired Superseti päringud.
2. **Kasutatavus ja liides**: ise teenindus (_self-service_) vs kureeritud juurdepääs. Semantikakiht (mõõdikud andmekogumi tasandil) aitab tagada ühtlustatud mõõdikuid kogu organisatsioonis.
3. **Turvalisus ja privaatsus**: kes näeb mida? Seotud praktikumiga 7 (RLS, maskimine). Serveerimisel tuleb otsustada, kas anda BI-tööriistale andmebaasi otseühendus ja kas API nõuab autentimist.
4. **Jälgitavus ja haldus**: kas andmed on värsked? Kellele andmestik kuulub? Kes vastutab, kui miski muutub? Seotud praktikumiga 6 (andmekvaliteet, OpenMetadata).

**Selles praktikumis** katame kaks serveerimisviisi: BI-näidikulaud (Superset, ülesanded 2–6) ja REST API pull (FastAPI, ülesanne 7).

---

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
│   ├── 01_load_data.py     # Laeb CSV → raw-skeem
│   └── 02_api.py           # FastAPI rakendus
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
- `POSTGRES_PASSWORD`: vali oma parool
- `SUPERSET_DB_PASSWORD`: vali oma parool
- `SUPERSET_SECRET_KEY`: genereeri juhuslik string
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- `API_KEY`: genereeri juhuslik string (kasutatakse ülesandes 7)
  ```bash
  python -c "import secrets; print(secrets.token_hex(24))"
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
jookseb. Ava brauser: **http://localhost:8088**. Logi sisse `.env`-s seadistatud
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
- `staging`: puhtad vaated raw-andmete pealt
- `marts`: koondtabelid Superseti jaoks.
  - `mart_myyk_kuus`: igakuine müük
  - `mart_myyk_kategooria`: müük tootekategooria ja kuu lõikes
  - `mart_myyk_piirkond`: müük piirkonna ja kuu lõikes

---

## Ülesanne 2: Superset, andmeühenduse loomine

1. Mine **Settings → Database Connections → + Database**
2. Vali andmebaasi tüüp: **PostgreSQL**
3. Täida ühenduse andmed:
   - Host: `db`
   - Port: `5432`
   - Database name: väärtus `.env`-st (`POSTGRES_DB`)
   - Username / Password: väärtused `.env`-st (`POSTGRES_USER` / `POSTGRES_PASSWORD`)
4. Klõpsa **Connect**, peaks näitama „Database connected"
5. Vajuta Finish

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

Mine **Datasets → + Dataset** ja registreeri :

| Skeem | Tabel |
|---|---|
| marts | mart_myyk_kuus |
| marts | mart_myyk_kategooria |
| marts | mart_myyk_piirkond |

Vasakul menüüs vali õige andmebaas, schema `marts` ja vastav tabel.  
Seejärel vajuta paremal all noolekest ning vali `Create dataset`

---

## Ülesanne 5: Diagrammide loomine

Diagramme saab luua `Charts` menüüst. 

### 5.1 Igakuine müük (joondiagramm)

- Dataset: **mart_myyk_kuus**
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

### 5.3 KPI: kogutulu (suur arv)

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
5. Lisa filter: **Date Range** → veerg `month_start` (vasakul menüüs, settings, Add or edit filters)
6. Salvesta ja avalda (**Publish**)

> **Parimate praktikate märkused**
>
> - **Sertifitseeritud andmekogum** (_Certified Dataset_): lisa andmekogumile sertifitseerimismärgis (**Edit dataset → Certified**), mis annab ärikasutajatele märku, et tegemist on usaldusväärse allikaga.
> - **Mõõdik andmekogumi tasandil**: defineeri `SUM(tulu_kokku)` üks kord andmekogumis (**Edit dataset → Metrics**), mitte igas diagrammis eraldi. See tagab ühtlustatud mõõdikud kõigis näidikulaudades.
> - **Rollipõhine juurdepääs**: ära anna BI-kasutajatele otse andmebaasi parooli. Kasuta Superseti sisest rollihaldust, kus `Alpha`-roll saab vaadata ja `Admin`-roll saab seadistada.
> - **Vahemälu**: lisa andmekogumile `cache_timeout` (sekundites), et Superset ei päriks iga kord andmebaasist. Sobiv väärtus sõltub andmete uuendamise sagedusest.

---

## Ülesanne 7: REST API andmete serveerimiseks

**Eesmärk:** sama mart-kiht, mis on Supersetis otseühenduse kaudu ligipääsetav
inimkasutajatele, tehakse REST API kaudu kättesaadavaks ka programmeeritavalt,
näiteks teistele rakendustele, ML-konveieritele või välispartneritele.

### 7.1 Käivita API

```bash
docker compose exec python uvicorn 02_api:app --host 0.0.0.0 --port 8000 --reload
```

API käivitub pordil 8000. Ava brauser: **http://localhost:8000/docs**. FastAPI
kuvab automaatselt interaktiivse dokumentatsiooni (Swagger UI).

### 7.2 Testi päringuid

Päringu saatmiseks on vaja API-võtit, mille väärtus on `.env`-failis (`API_KEY`).

```bash
# Korrektne päring, tagastab JSON-i
curl -H "X-API-Key: <sinu API_KEY väärtus>" http://localhost:8000/api/myyk/kuus

# Ilma võtmeta, tagastab 401 Unauthorized
curl http://localhost:8000/api/myyk/kuus
```

Saad katsetada ka brauseris, `docs` lehel vajuta tabaluku märki ja sisesta api võtme väärtus. 

Saadaval olevad lõpp-punktid:

| Lõpp-punkt | Andmestik |
|------------|-----------|
| `GET /api/myyk/kuus` | Igakuine müük (mart_myyk_kuus) |
| `GET /api/myyk/kategooria` | Müük kategooriate kaupa |
| `GET /api/myyk/piirkond` | Müük piirkondade kaupa |

### 7.3 Võrdle kahte serveerimisviisi

| | Superset (näidikulaud) | FastAPI (REST API) |
|--|------------------------|-------------------|
| Tarbija | Inimene | Rakendus / skript |
| Andmete vorming | Visuaalne | JSON |
| Autentimine | Superseti kasutajakonto | API-võti päises |
| Andmeallikas | Sama `marts`-skeem | Sama `marts`-skeem |
| Kasutuskoht | Brauser | `curl`, Python, mis tahes HTTP-klient |

### 7.4 Kuidas tehtaks päris elus?

Harjutuses kasutame lihtsat API-võtit, mis on piisav sisemiseks kasutuseks.
Toodangulahendus nõuab täiendavaid kihte.

**API turvalisus toodangus:**
- **OAuth 2.0 / JWT**: tööstusstandard. Lühiajalised tokenid, kasutaja identiteet ja ulatuspõhine (_scope_) juurdepääsukontroll. Kasutaja saab tokeni autentimisserverist, mitte otse API-lt.
- **API lüüs** (_API Gateway_, nt Kong, AWS API Gateway, nginx): lisab kiirusepiirangu (_rate limiting_), logimise ja ühtse sisenemispunkti kõigile teenustele.
- **mTLS** (_mutual TLS_): teenuste omavaheliseks suhtluseks. Mõlemad osapooled tõestavad oma identiteedi sertifikaadiga.
- API ei tohiks toodangus kunagi töötada ilma TLS-ita (HTTPS).

**Superseti ühendus andmebaasiga toodangus:**
Praegune lähenemine (kasutajanimi + parool `.env`-failis) sobib arenduseks. Toodangus:
- Superset peaks ühenduma **lugemisõigusega kasutajaga**, mitte administraatoriõigustega kasutajaga (vt praktikum 7: GRANT ja rollid).
- Andmebaas **ei tohiks olla avalikult ligipääsetav**: Superset ja DB peavad asuma samas privaatvõrgus.
- Parool `.env`-faili asemel **saladuste haldur** (_secrets manager_): HashiCorp Vault, AWS Secrets Manager, Kubernetes Secrets.
- Ühendusele lisatakse `sslmode=require`, mis tagab krüpteeritud ühenduse DB-ga.
- Suure koormusega süsteemides kasutatakse **ühendusepuhverdurit** (_connection pooler_) nagu PgBouncer, et vähendada ühenduste arvu andmebaasis.

---

## Lisaülesanne: Mõõdiku definitsioon

Vali üks kolmest mart-mudelist ja kirjuta **mõõdiku definitsioon**, mis vastab järgmistele küsimustele:

1. **Mida see mõõdik mõõdab?** (äriline tähendus)
2. **Kuidas arvutatakse?** (valem + filtrid)
3. **Millised on piirangud?** (mida see EI mõõda)
4. **Milline on detailsusaste?** (_granularity_: kuu? päev? pood?)

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
| **Detailsusaste** (_granularity_) | Andmerea täpsustase, nt üks rida kuu, kaupluse ja kategooria kohta |
| **REST API** | Veebistandard andmevahetuseks: klient saadab HTTP-päringu, server vastab JSON-iga |
| **API-võti** (_API key_) | Salajane tunnus päises, mis tõendab päringu saatja identiteeti |
| **Reverse ETL** | Andmete saatmine analüütikast tagasi operatiivsetesse süsteemidesse |
| **Saladuste haldur** (_secrets manager_) | Tööriist paroolide ja võtmete turvaliseks hoidmiseks (Vault, AWS Secrets Manager) |

## Viited

- [Apache Superset dokumentatsioon](https://superset.apache.org/docs/intro)
- [Superset SQL Lab](https://superset.apache.org/docs/using-superset/exploring-data)
- [dbt staging/marts muster](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- [FastAPI dokumentatsioon](https://fastapi.tiangolo.com)
- [Eesti IT-sõnastik (AKIT)](http://akit.cyber.ee)
