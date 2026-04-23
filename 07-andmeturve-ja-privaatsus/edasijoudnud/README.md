# Praktikum 7: Andmeturve ja privaatsus (Edasijõudnud)

## Eesmärk

Rakendada rollipõhist ligipääsukontrolli (RBAC), andmete maskeerimist ja auditit dbt-projektis. Praktikumi lõpuks on turvaloogika kirjeldatud koodis — `schema.yml` metaandmetes ja dbt makrodes — mitte käsitsi SQL-skriptides.

## Õpiväljundid

- Oskab lisada PII-metaandmeid dbt `schema.yml`-i ja kasutada neid maskeerimise makrodes
- Mõistab kolme turvatehnikat: vaatepõhine maskeerimine, Row-Level Security, Column-Level Security
- Teab, kuidas seadistada pgAudit ja lugeda auditiloge
- Näeb, millised turbeotsused kuuluvad koodi ja millised infrastruktuuri

## Eeldused

- Praktikumide 3 ja 6 materjal on läbitud (pg-duckdb, dbt, medaljoniarhitektuur tuttav)
- Docker ja Docker Compose on paigaldatud
- Andmebaasiklient: psql (konteineris saadaval) või DBeaver / DataGrip

## Arhitektuur

```
staging skeema          intermediate (view)      marts (table)         secured (view/table)
  users (toorandmed)  ->  int_users           ->  dim_users         ->  dim_users_analyst
  posts (toorandmed)  ->  int_posts           ->  fct_posts         ->  dim_users_marketing
                                                                    ->  dim_users_regional_base
                                                                    ->  fct_posts_analyst
```

**Rollid ja ligipääs:**

| Roll              | dim_users_analyst | dim_users_marketing | dim_users_regional_base | dim_users (marts) |
|-------------------|:-----------------:|:-------------------:|:-----------------------:|:-----------------:|
| `analyst`         | ✓ (PII maskeer.)  | —                   | —                       | —                 |
| `marketing`       | —                 | ✓ (PII puudub)      | —                       | —                 |
| `regional_manager`| —                 | —                   | ✓ (RLS + col-deny)      | —                 |
| `auditor`         | —                 | —                   | ✓ (täielik)             | ✓ (täielik)       |

## Arhitektuuriotsused

### Miks maskeerimine dbt-s, mitte andmebaasi natiivse Dynamic Data Masking abil?

**Probleem:** PII on toorkirjeteks andmebaasis olemas ja keegi võib sattu ligipääsule, kelle ei peaks.

**Variandid:**
- PostgreSQL 16+ Dynamic Data Masking laiendus (nt `anon` laiend) — töötab andmebaasi kihis transparentselt
- dbt vaated maskeerimisfunktsioonidega — maskeerimine on SQL-ina nähtav ja testitud
- Rakendusekihi maskeerimine — andmebaas annab toorandmed, rakendus maskeerib

**Valik:** dbt vaated, sest maskeerimine on versioonihalduses, dbt testide all ja DAGs nähtav. Kompromiss: maskeerimine ei rakendu väljaspool dbt-d loodud päringutele otse `staging`-skeemale.

### Miks meta-taggid `schema.yml`-is?

**Probleem:** PII-veergude loetelu hajub koodis laiali, raske ülevaade saada.

**Variandid:**
- Kommentaar SQL-failis — ei ole masinloetav
- Eraldi konfiguratsioonifail — kaksikekirje oht
- dbt `meta` taggid — integreeritud dbt lineage ja docs-ga

**Valik:** `meta.pii`, `meta.mask`, `meta.allowed_roles` `schema.yml`-is. `masked_columns` makro loeb neid compile-ajal ja genereerib rollipõhise SELECT-i. Kompromiss: kõik mudeli veerud peavad `schema.yml`-is defineeritud olema — nii on see ka hea praktika.

### Miks RLS tabelil, mitte vaatel?

**Probleem:** Vaadete puhul ei saa PostgreSQL RLS-i otse rakendada.

**Variandid:**
- Vaade WHERE-klausliga rolli-põhise tingimusega — staatiline, paindumatu
- Materialized view eraldi regiooni kaupa — tohutu hooldustaak
- RLS tabelil, sellele peale vaade — standard lähenemine

**Valik:** `dim_users_regional_base` on tabel RLS-iga, mitte vaade. `post_hook` seab `ENABLE ROW LEVEL SECURITY` ja loob `region_isolation` poliitika iga `dbt run` järel.

### Miks pgAudit, mitte `log_statement = all`?

**Probleem:** Vaja teada täpselt kes mida päris, sh millist tabelit ja mis rolliga.

**Variandid:**
- `log_statement = 'all'` — logib kõik SQL-laused ilma rolliinfota
- Triggerite põhine audit — kompleksne, mõjutab jõudlust kirjete kihil
- pgAudit — struktureeritud `AUDIT:` prefiksiga read, sisaldavad rolli, objekti, käsu tüüpi

**Valik:** pgAudit. Installimine: `postgresql-18-pgaudit` pakett `Dockerfile.db`-s, `shared_preload_libraries=pgaudit` `compose.yml` käsureal, `CREATE EXTENSION pgaudit` dbt `on-run-start` hookis.

## Kiirstart

```bash
# 1. Keskkond
cp .env.example .env
# Täida .env: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

# 2. Käivita konteinerid (esimene kord ehitab Dockerfile.db)
docker compose up -d --build

# 3. Laadi andmed staging skeemasse
docker compose exec python python ingest.py users
docker compose exec python python ingest.py posts

# 4. Loo andmebaasi rollid
docker compose exec dbt dbt run-operation create_roles

# 5. Ehita kõik mudelid (intermediate + marts + secured)
docker compose exec dbt dbt run

# 6. Käivita testid
docker compose exec dbt dbt test

# 7. Ava psql
docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

## Demo

### 1. Metaandmed dbt-s: PII ja maskeerimise taggid

Ava [dbt_project/models/marts/schema.yml](dbt_project/models/marts/schema.yml) ja vaata `dim_users` mudeli veerge:

```yaml
- name: email
  meta:
    pii: true
    mask: mask_email
    allowed_roles: ['analyst', 'auditor']

- name: city
  meta:
    pii: true
    mask: mask_varchar
    allowed_roles: ['analyst', 'marketing', 'auditor']

- name: country
  meta:
    pii: false   # riik ei ole PII, kasutatakse RLS filtreerimiseks
```

Taggid `meta.pii`, `meta.mask` ja `meta.allowed_roles` on masinloetavad — `masked_columns` makro ([macros/masked_columns.sql](dbt_project/macros/masked_columns.sql)) loeb neid `graph.nodes`-ist ja genereerib rollipõhise SELECT-loendi.

Maskeerimisfunktsioonid ([macros/masking.sql](dbt_project/macros/masking.sql)):

```sql
mask_email('email')    ->  left(email, 1) || '***@' || split_part(email, '@', 2)
                           'juhan.tamm@gmail.com'  ->  'j***@gmail.com'

mask_varchar('city')   ->  left(city, 1) || repeat('*', greatest(length(city) - 1, 0))
                           'Tallinn'  ->  'T******'

mask_date('registered_date')  ->  date_trunc('month', registered_date)::date
                                  '2019-07-15'  ->  '2019-07-01'
```

Secured mudel on tänu makrole ühe SELECT-lausega:

```sql
-- models/secured/dim_users_analyst.sql
SELECT
    {{ masked_columns('dim_users', role='analyst') }}
FROM {{ ref('dim_users') }}
```

Compile-ajal genereerib dbt täispäringu kõigi lubatud veergudega maskeerimisfunktsioonidega. Vaata kompileeritud SQL-i:

```bash
docker compose exec dbt dbt compile --select secured.dim_users_analyst
cat target/compiled/praktikum_07/models/secured/dim_users_analyst.sql
```

### 2. RBAC: rollid ja grants

Rollid luuakse `create_roles` makroga ([macros/roles.sql](dbt_project/macros/roles.sql)):

```bash
docker compose exec dbt dbt run-operation create_roles
```

`dbt run` seab igal mudelil grants:
- `dim_users_analyst` → `GRANT SELECT TO analyst` (config: `grants: {select: ['analyst']}`)
- `dim_users_marketing` → `GRANT SELECT TO marketing`
- `dim_users` (marts) → `GRANT SELECT TO auditor`

Kontrolli psql-is:

```sql
-- Vaata kõiki rolle
\du

-- Vaata secured skeema vaadete õigusi
\z secured.*
```

Rolli test psql-is (admin-kasutajana, kes on superuser, saab SET ROLE-ga mis tahes rolli võtta):

```sql
-- Analüütiku vaade: email maskeeritud, kõik veerud nähtavad
SET ROLE analyst;
SELECT user_key, first_name, email, city, registered_date
FROM secured.dim_users_analyst
LIMIT 3;

-- Turunduse vaade: PII veerud puuduvad vaatest täielikult
RESET ROLE;
SET ROLE marketing;
SELECT * FROM secured.dim_users_marketing LIMIT 3;

-- Näita et auditor näeb toore andmeid marts kihist
RESET ROLE;
SET ROLE auditor;
SELECT user_key, first_name, email, city FROM marts.dim_users LIMIT 3;
RESET ROLE;
```

### 3. Column-Level Security — Stsenaarium A: veerg puudub vaatest

`dim_users_marketing` vaatest puuduvad `first_name`, `last_name`, `full_name` ja `email` täielikult, sest `meta.allowed_roles` ei sisalda `marketing`-i ja `masked_columns` makro jätab need välja.

```sql
SET ROLE marketing;

-- Päring toimib — marketing näeb neid veerge
SELECT user_key, city, country, registered_date FROM secured.dim_users_marketing LIMIT 3;

-- Veerg puudub vaatest — viga tuleb kohe
SELECT email FROM secured.dim_users_marketing;
-- ERROR:  column "email" does not exist

RESET ROLE;
```

Kontrolli dbt testiga:

```bash
docker compose exec dbt dbt test --select assert_marketing_no_email_column
```

### 4. Column-Level Security — Stsenaarium B: veerg on olemas aga keelatud (Column-Level Grant)

`dim_users_regional_base` on tabel (mitte vaade), mis sisaldab ka `email` veergu. `post_hook` annab `regional_manager`-ile `GRANT SELECT (user_key, user_id, first_name, ...)` ainult valitud veergudele — `email`-i ei ole nimekirjas.

```sql
SET ROLE regional_manager;

-- Lubatud veerud töötavad
SELECT user_key, first_name, city, country
FROM secured.dim_users_regional_base
LIMIT 3;

-- email veerg on tabelis olemas aga grant puudub
SELECT email FROM secured.dim_users_regional_base;
-- ERROR:  permission denied for column "email"

RESET ROLE;
```

Kontrolli dbt testiga:

```bash
docker compose exec dbt dbt test --select assert_regional_no_email_grant
```

Vaata PostgreSQL süsteemikataloogist mida regional_manager näeb:

```sql
SELECT grantee, column_name, privilege_type
FROM information_schema.column_privileges
WHERE table_schema = 'secured'
  AND table_name = 'dim_users_regional_base'
ORDER BY column_name;
```

### 5. Row-Level Security (RLS)

`dim_users_regional_base` tabelil on RLS-poliitika ([macros/rls.sql](dbt_project/macros/rls.sql)):

```sql
CREATE POLICY region_isolation ON secured.dim_users_regional_base
  FOR SELECT
  TO regional_manager
  USING (country = current_setting('app.current_region', true));
```

Seansi-muutuja `app.current_region` määrab, milliseid ridu regional_manager näeb. Kui muutuja pole seatud, tagastab `current_setting(..., true)` `NULL` ja ükski rida ei läbi filtrit — turvaline vaikekäitumine.

```sql
SET ROLE regional_manager;

-- Ilma regiooni seadmiseta: tühi tulemus
SELECT country, city FROM secured.dim_users_regional_base;
-- (0 rows)

-- Seame regiooni
SET app.current_region = 'Finland';
SELECT country, city, first_name FROM secured.dim_users_regional_base;
-- Näitab ainult Soome kasutajaid

-- Vaheta regioon ümber
SET app.current_region = 'Germany';
SELECT country, city FROM secured.dim_users_regional_base;
-- Näitab ainult Saksamaa kasutajaid

-- Kontrolli poliitikaid süsteemikataloogist
RESET ROLE;
SELECT polname, polcmd, polroles::regrole[]
FROM pg_policies
WHERE tablename = 'dim_users_regional_base';
```

### 6. pgAudit: kes mida päris

Ava teises terminalis auditilogi jälgimine:

```bash
docker compose logs -f db 2>&1 | grep AUDIT
```

Tee päringuid (esimeses terminalis psql-is):

```sql
SET ROLE analyst;
SELECT email FROM secured.dim_users_analyst LIMIT 1;
RESET ROLE;

SET ROLE auditor;
SELECT * FROM marts.dim_users LIMIT 1;
RESET ROLE;
```

Logis ilmub iga päringu kohta rida formaadis:

```
AUDIT: SESSION,1,1,READ,SELECT,TABLE,secured.dim_users_analyst,"SELECT email ...",<none>
```

Väljad: `AUDIT: SESSION, statement_id, substatement_id, class, command, object_type, object_name, statement, parameter`.

pgAudit logib:
- `READ` — SELECT-laused (sh mis tabelist/vaatest)
- `WRITE` — INSERT/UPDATE/DELETE
- `ROLE` — GRANT/REVOKE/CREATE ROLE
- `DDL` — CREATE/DROP/ALTER

Leia kõik `email`-veeru päringud:

```bash
docker compose logs db 2>&1 | grep "AUDIT" | grep "email"
```

Seadistuse vaata compose.yml `-c` parameetritest:

```
pgaudit.log = read,write,role,ddl   # mida logida
pgaudit.log_relation = on           # tabeli nimi igal real
pgaudit.log_parameter = on          # pärimisparameetrid
```

## Ülesanded

### Ülesanne 1: Uus roll `finance_analyst`

Finantsosakond soovib näha postituste statistikat ja kasutajate registreerumiskuud, kuid mitte nimesid, e-posti ega linnu.

**Samm 1.** Vaata `models/marts/schema.yml`-is `dim_users` ja `fct_posts` mudeli `allowed_roles` liste. Tuvasta, millised veerud `finance_analyst` peaks nägema (registreerumiskuupäev, riik, user_key, user_id, post_id, body_length, loaded_at).

**Samm 2.** Lisa `finance_analyst` allowed_roles listidesse ainult nende veergude juurde, mida finantsosakond vajab.

**Samm 3.** Lisa `finance_analyst` `macros/roles.sql` `create_roles` makro ARRAY-i ja käivita:
```bash
docker compose exec dbt dbt run-operation create_roles
```

**Samm 4.** Loo failid `models/secured/dim_users_finance.sql` ja `models/secured/fct_posts_finance.sql`, mis kasutavad `masked_columns` makrot rolliga `finance_analyst`.

**Samm 5.** Ehita uued mudelid ja kontrolli:
```bash
docker compose exec dbt dbt run --select secured.dim_users_finance secured.fct_posts_finance
```

```sql
SET ROLE finance_analyst;
SELECT * FROM secured.dim_users_finance LIMIT 3;
-- Peaks näitama ainult: user_key, user_id, country, registered_date (kuutäpsusega)

SELECT email FROM secured.dim_users_finance;
-- ERROR: column "email" does not exist
RESET ROLE;
```

### Ülesanne 2: RLS keerulisema tingimusega

Lisa `fct_posts_analyst` vaatele RLS, kus `analyst` näeb ainult postitusi, mille `body_length > 200`. See demonstreerib, et RLS USING-klausel võib olla mistahes SQL-avaldis.

**Samm 1.** Muuda `fct_posts_analyst.sql` nii, et see on tabel (`materialized='table'`), mitte vaade (RLS nõuab tabelit).

**Samm 2.** Lisa `post_hook`:
```sql
ALTER TABLE {{ this }} ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS long_posts_only ON {{ this }};
CREATE POLICY long_posts_only ON {{ this }}
  FOR SELECT TO analyst
  USING (body_length > 200);
```

**Samm 3.** Käivita `dbt run --select secured.fct_posts_analyst` ja kontrolli:
```sql
SET ROLE analyst;
SELECT post_id, body_length FROM secured.fct_posts_analyst ORDER BY body_length LIMIT 5;
-- Kõik tulemused peaks olema body_length > 200
RESET ROLE;
```

**Küsi endalt:** kas see on jõudluse mõttes hea lähenemine, kui andmeid on miljoneid?

### Ülesanne 3: Auditilogi analüüs

Tee järgmised päringud erinevate rollidega ja analüüsi pgAudit logi:

```sql
-- Tee need päringud järjest
SET ROLE analyst;   SELECT email FROM secured.dim_users_analyst;    RESET ROLE;
SET ROLE marketing; SELECT * FROM secured.dim_users_marketing;      RESET ROLE;
SET ROLE auditor;   SELECT email FROM marts.dim_users LIMIT 1;      RESET ROLE;
```

Kogu logid:
```bash
docker compose logs db 2>&1 | grep "AUDIT" > /tmp/audit.log
```

Vasta küsimustele logiread vaadates:
1. Mis `object_name` on kirjas, kui `analyst` päriss `secured.dim_users_analyst`-ist?
2. Kas marketing-rolli päring logiti? Mis rollinime all?
3. Mis vahe on logis `READ` ja `DDL` kirjete vahel?

## Tõrkeotsing

### pgAudit extension ei aktiveeru

**Sümptom:** `dbt run` annab vea `could not open extension control file ".../pgaudit.control"`

**Diagnoos:** pgaudit pakett pole installitud

```bash
docker compose exec db apt list --installed 2>/dev/null | grep pgaudit
```

**Lahendus:** Kontrolli et `Dockerfile.db` ehitamine õnnestus:
```bash
docker compose build db
docker compose up -d db
```

Kui `postgresql-18-pgaudit` paketti ei leia repodest, lisa `ensure_pgaudit_extension` makrosse kommentaar ja jäta `on-run-start` hook vahele — praktikum töötab ka ilma pgAudit-ita, kasutades `log_statement = all`.

### SET ROLE ei tööta

**Sümptom:** `SET ROLE analyst` annab `ERROR: role "analyst" does not exist`

**Lahendus:** Käivita rollide loomine:
```bash
docker compose exec dbt dbt run-operation create_roles
```

### RLS ei filtreeri

**Sümptom:** `SET ROLE regional_manager` + `SELECT * FROM secured.dim_users_regional_base` tagastab kõik read

**Diagnoos:** RLS-poliitika puudub tabelilt:
```sql
SELECT * FROM pg_policies WHERE tablename = 'dim_users_regional_base';
```

**Lahendus:** Käivita `dbt run --select secured.dim_users_regional_base` — `post_hook` loob poliitika uuesti.

### `masked_columns` makro tagastab tühja tulemuse

**Sümptom:** Kompileeritud SQL-is on `SELECT` järel tühi

**Diagnoos:** `graph.nodes`-is ei leita mudeli veerge — `schema.yml` puudub või on valesid veergude nimesid

**Lahendus:** Kontrolli et kõik `dim_users` veerud on `models/marts/schema.yml`-is defineeritud täpselt sama nimega mis `dim_users.sql`-is.
