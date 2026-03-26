# Andmeinseneeria 2026 — Praktikumid

Tartu Ülikooli andmeinseneeria kursuse praktikumimaterjalid. Kursus koosneb 9 nädalast, millest igaüks käsitleb ühte andmeinseneeria põhiteemat. Iga nädal pakub kahte rada:

- **Baastase** — samm-sammult juhendatud praktikum, mis sobib teemaga esmatutvujale
- **Edasijõudnud** — kiirema tempo ja suurema iseseisvusega rada, mis eeldab varasemat kogemust

## Eeldused

Vaata [common-setup](./common-setup/README.md) kausta Docker ja muude tööriistade paigaldusjuhiste jaoks.

## Nädalate ülevaade

### [01 — Andmeinseneeria alused](./01-andmeinseneeria-alused/)

Sissejuhatus andmeinseneeriasse: Docker, PostgreSQL, CSV laadimine ja esimene andmetöövoo harjutus.

- [Baastase](./01-andmeinseneeria-alused/baastase/README.md) — PostgreSQL-iga ühenduse loomine, CSV-faili laadimine, töövoo põhiloogika
- [Edasijõudnud](./01-andmeinseneeria-alused/edasijoudnud/README.md) — Python ETL, REST API, andmete normaliseerimine, idempotentsus

### [02 — Andmemudelid ja baasid](./02-andmemudelid-ja-baasid/)

Relatsiooniline ja dimensionaalne andmete modelleerimine. Star schema kavandamine ja ehitamine.

- [Baastase](./02-andmemudelid-ja-baasid/baastase/README.md) — lihtne tähtskeemi loomine, faktitabel ja dimensioonid, SQL joinid ja agregatsioonid
- [Edasijõudnud](./02-andmemudelid-ja-baasid/edasijoudnud/README.md) — Kimballi metoodika, SCD Type 2, päringu jõudluse analüüs

### [03 — Andmete integreerimine](./03-andmete-integreerimine/)

Andmete kogumine failidest ja API-dest, puhastamine ja laadimine andmebaasi. Transformatsioonitööriistad (dbt).

- [Baastase](./03-andmete-integreerimine/baastase/README.md) — CSV/Parquet/API allikast laadimine, andmete puhastamine, ETL etappide selgitamine
- [Edasijõudnud](./03-andmete-integreerimine/edasijoudnud/README.md) — inkrementaalne laadimine, idempotentsus, logitud ja veahaldusega ETL

### [04 — Andmetorude orkestreerimine](./04-andmetorude-orkestreerimine/)

Andmetorustiku automatiseerimine. Ajastamine, sõltuvused ja orkestreerimise põhimõtted.

- [Baastase](./04-andmetorude-orkestreerimine/baastase/README.md) — CRON ajastus, logide kogumine, sõltuvuste ja retry põhimõtted
- [Edasijõudnud](./04-andmetorude-orkestreerimine/edasijoudnud/README.md) — Airflow DAG, operaatorid, sõltuvused, backfill

### [05 — Suurandmed ja pilvelahendused](./05-suurandmed-ja-pilvelahendused/)

Suurandmete põhimõtted, pilve kasutusloogika ja kaasaegsed andmeformaadid.

- [Baastase](./05-suurandmed-ja-pilvelahendused/baastase/README.md) — Parquet, avatud tabeliformaadid, hajussüsteemid, Databricks sissejuhatus
- [Edasijõudnud](./05-suurandmed-ja-pilvelahendused/edasijoudnud/README.md) — Spark DataFrame transformatsioonid, partitsioneerimine, data lakehouse

### [06 — Andmekvaliteet ja andmehaldus](./06-andmekvaliteet-ja-haldus/)

Kvaliteedikontrollid andmetöövoogudes. Andmete dokumenteerimine ja metaandmete haldamine.

- [Baastase](./06-andmekvaliteet-ja-haldus/baastase/README.md) — kvaliteedireeglid, vigaste ridade tuvastamine, andmekataloogide väärtus
- [Edasijõudnud](./06-andmekvaliteet-ja-haldus/edasijoudnud/README.md) — automatiseeritud testid, kvaliteediraport, data lineage, andmekataloogi roll

### [07 — Andmeturve ja privaatsus](./07-andmeturve-ja-privaatsus/)

Ligipääsud, rollid ja tundlike andmete käsitlemine. Minimaalõiguste printsiip.

- [Baastase](./07-andmeturve-ja-privaatsus/baastase/README.md) — PII, rollipõhine ligipääs, saladuste turvaline hoidmine
- [Edasijõudnud](./07-andmeturve-ja-privaatsus/edasijoudnud/README.md) — andmete maskeerimine, audit logid, GDPR, row-level security

### [08 — Reaalajas andmetöötlus](./08-reaalajas-andmetootlus/)

Sündmuspõhine arhitektuur ja voogandmete (streaming) töötlemine.

- [Baastase](./08-reaalajas-andmetootlus/baastase/README.md) — sündmused, publish/subscribe simulatsioon, batch vs streaming
- [Edasijõudnud](./08-reaalajas-andmetootlus/edasijoudnud/README.md) — Apache Kafka, topic/partition/consumer group, voogandmete transformatsioonid

### [09 — Ärianalüütika ja andmete serveerimine](./09-arianalyytika-ja-serveerimine/)

Tehniline töö seotud äriväärtusega. Dashboardid, KPI-d ja andmepõhine lugu.

- [Baastase](./09-arianalyytika-ja-serveerimine/baastase/README.md) — lihtne dashboard, KPI-de selgitamine, andmetest järelduste tegemine
- [Edasijõudnud](./09-arianalyytika-ja-serveerimine/edasijoudnud/README.md) — esitlusvalmis demo, mõõdikute definitsioonid, seos kvaliteedi ja turvalisusega
