# Praktikum 3: Andmete integreerimine API ja CSV abil

## Sisukord

- [Praktikumi eesmärk](#praktikumi-eesmärk)
- [Õpiväljundid](#õpiväljundid)
- [Hinnanguline ajakulu](#hinnanguline-ajakulu)
- [Eeldused](#eeldused)
- [Enne alustamist](#enne-alustamist)
- [Praktikumi failid](#praktikumi-failid)
- [Kus praktikumi failid asuvad?](#kus-praktikumi-failid-asuvad)
- [Miks see teema on oluline?](#miks-see-teema-on-oluline)
- [Uued mõisted](#uued-mõisted)
- [ETL etapid selles praktikumis](#etl-etapid-selles-praktikumis)
- [Soovitatud töötee](#soovitatud-töötee)
- [1. Ava õige kaust](#1-ava-õige-kaust)
- [2. Loo `.env` fail](#2-loo-env-fail)
- [3. Käivita konteinerid](#3-käivita-konteinerid)
- [4. Vaata üle põhiallikad](#4-vaata-ule-pohiallikad)
- [5. Loo skeemad ja tabelid](#5-loo-skeemad-ja-tabelid)
- [6. Laadi CSV-fail staging-tabelisse](#6-laadi-csv-fail-staging-tabelisse)
- [7. Vaata valmis ETL-skripti](#7-vaata-valmis-etl-skripti)
- [8. Käivita ETL](#8-kaivita-etl)
- [9. Kontrolli tulemust SQL-iga](#9-kontrolli-tulemust-sql-iga)
- [10. Kontrolli idempotentsust](#10-kontrolli-idempotentsust)
- [Kontrollpunktid](#kontrollpunktid)
- [Levinud vead ja lahendused](#levinud-vead-ja-lahendused)
- [Kokkuvõte](#kokkuvote)
- [Lisaülesanded](#lisauesanded)
- [Koristamine](#koristamine)

## Praktikumi eesmärk

Selle praktikumi eesmärk on teha läbi esimene töötav andmete integreerimise töövoog nii, et õppija ei peaks Pythoni osa ise nullist kirjutama.

Põhivoos kasutame kahte allikat:

- avalikku `API`-t;
- kohalikku `CSV` faili.

Kolmas allikas, kohalik `JSON` fail, jääb lisaülesandesse. Seal saad olemasoleva töötava näite põhjal proovida, kuidas laiendada sama töövoogu kolme allika peale.

## Õpiväljundid

Praktikumi lõpuks oskad:

- käivitada baastaseme 3. praktikumi keskkonna `docker compose` abil;
- laadida `CSV` faili staging-tabelisse;
- käivitada valmis Pythoni `ETL` skripti, mis loeb andmeid `API`-st;
- selgitada, kuidas `API` ja `CSV` andmed ühendatakse ühe võtme alusel;
- kontrollida `SQL` päringutega, kas andmed jõudsid õigesse tabelisse;
- kirjeldada, miks sama töö saab turvaliselt uuesti käivitada.

## Hinnanguline ajakulu

Arvesta umbes 2 tunniga.

See aeg jaguneb ligikaudu nii:

- 20 min keskkonna käivitamiseks ja failidega tutvumiseks;
- 25 min skeemade ja tabelite loomiseks;
- 20 min `CSV` faili laadimiseks ja kontrollimiseks;
- 25 min valmis `ETL` skripti läbivaatamiseks ja käivitamiseks;
- 30 min tulemuse kontrollimiseks ja korduskäivituse proovimiseks.

Lisaülesanded ei pea mahtuma praktikumi põhiaja sisse.

## Eeldused

Sul on vaja:

- VS Code'i või GitHub Codespacesit;
- terminali;
- töötavat Dockeri keskkonda, kui teed praktikumi oma arvutis;
- selle repositooriumi faile.

See praktikum eeldab, et eelmistest baastaseme praktikumidest on tuttavad vähemalt järgmised sammud:

- oskad avada õige kausta;
- oskad luua `.env` faili `.env.example` põhjal;
- oskad käivitada käsu `docker compose up -d`;
- oskad avada `psql` kliendi käsuga `docker compose exec db psql ...`;
- tead, et osa käske käib hosti terminalis ja osa `psql` sees.

Kui need sammud on veel ebakindlad, vaata vajadusel uuesti:

- [Praktikum 1: PostgreSQL-iga ühenduse loomine ja esimese CSV-faili laadimine](../../01-andmeinseneeria-alused/baastase/README.md)
- [Praktikum 2: Lihtne faktitabel ja kaks dimensiooni](../../02-andmemudelid-ja-baasid/baastase/README.md)

## Enne alustamist

### Soovitatud keskkond

Praktikumi tegemiseks sobib hästi järgmine tööviis:

- avad kausta `03-andmete-integreerimine/baastase` VS Code'is;
- kasutad VS Code'i sisseehitatud terminali;
- käivitad kõik käsud samas terminaliaknas;
- avad `SQL`, `CSV`, `JSON` ja `Python` failid VS Code'is.

See on algajale kõige vähem segadust tekitav tööviis.

### Kuidas saada kätte selle nädala failid?

Kui sul on repositoorium juba eelmiste nädalate tööde jaoks olemas, uuenda enne alustamist failid.

Kui kasutasid `git clone` käsku:

```bash
git status
git pull
```

Kui `git pull` ütleb, et sul on pooleli kohalikke muudatusi ja sa ei tea, kuidas neid lahendada, siis kõige turvalisem tee on teha praktikumi jaoks uus puhas koopia.

Kui laadisid repositooriumi varem alla `ZIP` failina:

1. ava repositoorium GitHubis;
2. vali `Code`;
3. vali `Download ZIP`;
4. paki fail lahti uude kausta;
5. ava see uus kaust VS Code'is.

## Praktikumi failid

Kõik allpool toodud suhtelised failiteed eeldavad, et asud kaustas `03-andmete-integreerimine/baastase`.

- [`compose.yml`](./compose.yml) kirjeldab andmebaasi- ja Pythoni konteinerit
- [`.env.example`](./.env.example) sisaldab ühenduse näidisväärtusi
- [`Dockerfile.python`](./Dockerfile.python) ehitab Pythoni konteineri
- [`data/kasutaja_staatus.csv`](./data/kasutaja_staatus.csv) on põhiraja `CSV` allikas
- [`data/teavituseelistused.json`](./data/teavituseelistused.json) on lisaülesande `JSON` allikas
- [`scripts/01_create_tables.sql`](./scripts/01_create_tables.sql) loob põhiraja skeemad ja tabelid
- [`scripts/02_load_user_status.sql`](./scripts/02_load_user_status.sql) laadib `CSV` faili `staging` tabelisse
- [`scripts/03_check_staging.sql`](./scripts/03_check_staging.sql) aitab staging-andmeid kontrollida
- [`scripts/03_integrate_users.py`](./scripts/03_integrate_users.py) on valmis kahe allika `ETL` skript koos Pythoni süntaksit selgitavate kommentaaridega
- [`scripts/04_check_results.sql`](./scripts/04_check_results.sql) sisaldab lõppkontrolli päringuid
- [`scripts/lisa_01_prepare_preferences.sql`](./scripts/lisa_01_prepare_preferences.sql) valmistab lisaülesande jaoks ette kolmanda allika tabeli ja lisaväljad
- [`scripts/lisa_03_integrate_users_template.py`](./scripts/lisa_03_integrate_users_template.py) on lisaülesande mall kolme allika ühendamiseks
- [`scripts/naidis_lahendused/lisa_03_integrate_users_lahendus.py`](./scripts/naidis_lahendused/lisa_03_integrate_users_lahendus.py) on üks võimalik lahendus lisaülesandele
- [`scripts/99_reset.sql`](./scripts/99_reset.sql) puhastab praktikumi skeemad
- [`scripts/requirements.txt`](./scripts/requirements.txt) loetleb Pythoni teegid

## Kus praktikumi failid asuvad?

Selles praktikumis on korraga kasutusel kolm konteksti.

- Host ehk sinu arvuti või Codespace'i tööruum
- Andmebaasi konteiner `db`
- Pythoni konteiner `python`

Sama fail võib olla eri kontekstides eri teega.

Näited:

- hostis on fail `data/kasutaja_staatus.csv`
- andmebaasi konteineri sees on sama fail `/data/kasutaja_staatus.csv`
- Pythoni konteineri sees on sama fail samuti `/data/kasutaja_staatus.csv`

Sama kehtib `scripts` kausta kohta:

- hostis on fail `scripts/03_integrate_users.py`
- konteineri sees on see fail `/scripts/03_integrate_users.py`

See vahe on oluline kahel põhjusel:

- `psql` loeb `\copy` käsus faili konteineri vaatest;
- Pythoni skript ühendub andmebaasiga konteineri sisevõrgu kaudu nimega `db`.

## Miks see teema on oluline?

Tööelus tuleb väga sageli ette olukord, kus üks allikas on süsteemi `API` ja teine allikas on fail.

Näiteks:

- äri- või registrisüsteem annab sulle `API` vastuse;
- mõni teine süsteem saadab kõrvale väikese `CSV` ekspordi.

Andmete integreerimine tähendab siin vähemalt nelja asja:

- tuua andmed erinevatest allikatest kätte;
- leida ühine võti, mille järgi neid seostada;
- puhastada see võti enne ühendamist;
- laadida tulemus tabelisse, mida saab hiljem pärida.

Selles praktikumis teeme just selle väikese põhiloogika läbi.

## Uued mõisted

### `API`

`API` tähendab `Application Programming Interface`, eesti keeles rakendusliidest.

Selles praktikumis tähendab see kohta, kust Pythoni skript saab kasutajate andmed `HTTP` päringuga kätte.

### `CSV`

`CSV` tähendab `Comma-Separated Values`, eesti keeles komadega eraldatud tabelandmeid tekstifailis.

Selles praktikumis tuleb `CSV` failist kasutaja staatus.

### `Staging`

`Staging` on vahekiht, kuhu paneme andmed enne lõplikku kasutustabelit.

Selles praktikumis kasutame `staging` skeema selleks, et hoida:

- `CSV` failist tulnud kasutajastaatused;
- `API`-st tulnud kasutajad.

### Idempotentsus

Idempotentsus tähendab, et sama töö korduv käivitamine annab sama lõpptulemuse.

Selles praktikumis saavutame selle lihtsal viisil:

- tühjendame väikesed sihttabelid enne uut laadimist;
- laeme samad andmed uuesti sisse.

See ei ole ainus võimalik lahendus, aga baastasemel on see hästi jälgitav.

## ETL etapid selles praktikumis

Selle praktikumi töövoog jaguneb kolmeks etapiks.

### `Extract`

Andmete kättesaamine allikatest.

Selles praktikumis tähendab see:

- kasutajate lugemist `API`-st;
- kasutajastaatuste võtmist `CSV` failist, mis on enne staging-tabelisse laaditud.

### `Transform`

Andmete puhastamine ja ühendamine.

Selles praktikumis tähendab see:

- e-posti aadressi puhastamist;
- vajalike väljade valimist;
- `API` ja `CSV` andmete ühendamist ühe e-posti aadressi alusel.

### `Load`

Andmete kirjutamist sihtkohta.

Selles praktikumis tähendab see:

- `API` kasutajate salvestamist tabelisse `staging.api_users`;
- lõpptulemuse salvestamist tabelisse `analytics.user_profile`.

## Soovitatud töötee

Praktikumi tööjärjekord on järgmine.

1. Ava õige kaust.
2. Loo `.env` fail.
3. Käivita konteinerid.
4. Vaata üle põhiraja allikad.
5. Loo tabelid.
6. Laadi `CSV` tabelisse.
7. Vaata valmis `ETL` skript läbi.
8. Käivita töö.
9. Kontrolli tulemust.

See tööjärjekord hoiab põhiraja lihtsa ja jälgitavana. Pythoni koodi täiendamine tuleb alles lisaülesandes.

## 1. Ava õige kaust

See samm tehakse hosti terminalis.

Liigu praktikumi kausta:

```bash
cd 03-andmete-integreerimine/baastase
```

Soovi korral kontrolli asukohta.

macOS-is, Linuxis ja Codespacesis:

```bash
pwd
```

Windows PowerShellis:

```powershell
Get-Location
```

## 2. Loo `.env` fail

See samm tehakse hosti terminalis.

macOS-is, Linuxis ja Codespacesis:

```bash
cp .env.example .env
```

Windows PowerShellis:

```powershell
Copy-Item .env.example .env
```

Vaikimisi väärtused on:

- kasutaja `praktikum`
- parool `praktikum`
- andmebaas `praktikum`

Praegu ei ole vaja neid muuta.

## 3. Käivita konteinerid

See samm tehakse hosti terminalis.

Käivita andmebaas ja Pythoni konteiner:

```bash
docker compose up -d --build
```

Kontrolli, et teenused käivitusid:

```bash
docker compose ps
```

Oodatav tulemus:

- teenus `db` on olekus `running` või `healthy`
- teenus `python` on olekus `running`

Kui tahad näha andmebaasi viimaseid logisid:

```bash
docker compose logs db --tail=20
```

## 4. Vaata üle põhiallikad

See samm tehakse hostis VS Code'i failivaates.

Põhiraja kaks allikat on:

1. avalik `API`: `https://jsonplaceholder.typicode.com/users`
2. kohalik `CSV` fail [`data/kasutaja_staatus.csv`](./data/kasutaja_staatus.csv)

Vaata need lühidalt üle ja pööra tähelepanu järgmisele:

- `CSV` failis on e-posti aadressides eri kujusid, näiteks suured tähed ja tühikud;
- `API` vastuses on kasutaja linn ja ettevõtte nimi pesastatud kujul;
- mõlemat allikat saab ühendada e-posti alusel, aga enne tuleb e-post puhastada.

Samas kaustas on ka fail [`data/teavituseelistused.json`](./data/teavituseelistused.json), kuid põhirajal me seda veel ei kasuta. See tuleb mängu lisaülesandes.

## 5. Loo skeemad ja tabelid

See samm tehakse kõigepealt hosti terminalis, seejärel `psql` sees.

Ava `psql` andmebaasi konteineri sees:

```bash
docker compose exec db psql -U praktikum -d praktikum
```

Kui `psql` on avanenud, käivita tabelite loomise skript:

```sql
\i /scripts/01_create_tables.sql
```

Kontrolli, et skeemad tekkisid:

```sql
\dn
```

Kontrolli, et tabelid tekkisid:

```sql
\dt staging.*
\dt analytics.*
```

Oodatav tulemus:

- skeemad `staging` ja `analytics`
- tabelid `staging.user_status`, `staging.api_users` ja `analytics.user_profile`

## 6. Laadi CSV-fail staging-tabelisse

See samm tehakse endiselt `psql` sees.

See on töövoo ettevalmistav samm, mis teeb `CSV` allika skriptile kättesaadavaks.

Põhiraja `ETL` loogikas on see osa sellest, kuidas teine allikas jõuab staging-kihti enne ühendamist.

Käivita `CSV` laadimise skript:

```sql
\i /scripts/02_load_user_status.sql
```

Siis kontrolli, mida tabelisse laeti:

```sql
\i /scripts/03_check_staging.sql
```

Pööra tähelepanu sellele, et e-posti väljad ei ole veel puhastatud.

See on tahtlik. Toorandmed võivadki jõuda staging-tabelisse täpselt sellisena, nagu need allikast tulid.

Kui oled kontrolli lõpetanud, välju `psql`-ist:

```sql
\q
```

## 7. Vaata valmis ETL-skripti

See samm tehakse hostis VS Code'i redaktoris.

Ava fail [`scripts/03_integrate_users.py`](./scripts/03_integrate_users.py).

Sa ei pea selles etapis skripti muutma. Eesmärk on saada aru, mida valmis töövoog teeb.

Failis on nüüd sees ka pikemad kommentaarid, mis aitavad jälgida nii `ETL` loogikat kui ka Pythoni süntaksit.

Vaata läbi neli kohta. Need vastavad `ETL` etappidele nii:

1. `Extract`: `fetch_api_users` loeb kasutajad `API`-st
2. `Extract`: `read_status_lookup` loeb `CSV` failist staging-tabelisse jõudnud staatused
3. `Transform`: `normalize_email` puhastab ühendusvõtme ja `build_final_rows` ühendab andmed
4. `Load`: `load_api_users` ja `load_final_rows` kirjutavad andmed tabelitesse

See on selles kursuses esimene täielikult läbi mängitud `ETL` näide.

## 8. Käivita ETL

See samm tehakse hosti terminalis.

Käivita valmis skript:

```bash
docker compose exec python python /scripts/03_integrate_users.py
```

Oodatav tulemus on umbes selline:

```text
ETL etapp 1/3: Extract
- API-st tuli 10 kasutajat.
- Staging-tabelist tuli 10 staatusekirjet.
ETL etapp 2/3: Transform
- Puhastasin e-posti ja ühendasin andmed 10 kasutaja jaoks.
ETL etapp 3/3: Load
- Laadisin staging.api_users tabelisse 10 rida.
- Laadisin analytics.user_profile tabelisse 10 rida.
Valmis.
```

Kui skript annab veateate, loe see rahulikult läbi.

Kõige sagedasemad vead selles kohas on:

- `API` päring ei õnnestu;
- andmebaasi tabelid ei ole veel loodud;
- `CSV` faili pole enne staging-tabelisse laaditud.

## 9. Kontrolli tulemust SQL-iga

See samm tehakse taas `psql` sees.

Ava `psql`:

```bash
docker compose exec db psql -U praktikum -d praktikum
```

Käivita kontrollpäringud:

```sql
\i /scripts/04_check_results.sql
```

Vaata eriti järgmisi küsimusi:

- kas `staging.api_users` sisaldab 10 rida;
- kas `analytics.user_profile` sisaldab 10 rida;
- kas e-posti aadressid on nüüd väikeste tähtedega ja ilma üleliigsete tühikuteta;
- kas mõnel kasutajal on `account_status` puudu.

See viimane küsimus on oluline. Integreerimisel ei olegi alati igas allikas kõigi kirjete kohta täielikku infot.

Kui oled tulemuse üle vaadanud, välju `psql`-ist:

```sql
\q
```

## 10. Kontrolli idempotentsust

See samm tehakse hosti terminalis.

Käivita sama skript teist korda:

```bash
docker compose exec python python /scripts/03_integrate_users.py
```

Seejärel kontrolli, et ridade arv ei kasvanud:

```bash
docker compose exec db psql -U praktikum -d praktikum -c "SELECT COUNT(*) FROM analytics.user_profile;"
```

Oodatav tulemus on ikka `10`.

Mida see näitab?

- töö on selles väikeses näites idempotentne;
- korduv käivitamine ei tekita duplikaate;
- andmetoru saab vajadusel uuesti käivitada.

## Kontrollpunktid

Praktikumi keskel ja lõpus saad end kontrollida nende punktide abil.

### Pärast konteinerite käivitamist

- `docker compose ps` näitab teenuseid `db` ja `python`
- `db` teenus on `healthy` või `running`

### Pärast tabelite loomist

- `\dn` näitab skeemasid `staging` ja `analytics`
- `\dt staging.*` näitab kahte staging-tabelit

### Pärast `CSV` laadimist

- `staging.user_status` sisaldab 10 rida
- tabelis on näha puhastamata e-posti väljad

### Pärast `ETL` skripti käivitamist

- `staging.api_users` sisaldab 10 rida
- `analytics.user_profile` sisaldab 10 rida

## Levinud vead ja lahendused

### Sümptom: `docker compose up -d --build` ebaõnnestub

Tõenäoline põhjus:

- Docker ei tööta või ei ole käivitatud

Lahendus:

- ava Docker Desktop või kontrolli, et sinu Dockeri teenus töötab
- proovi käsku uuesti

### Sümptom: `could not translate host name "db"`

Tõenäoline põhjus:

- käivitasid Pythoni väljaspool konteinerit

Lahendus:

- kasuta käsku `docker compose exec python python /scripts/03_integrate_users.py`
- ära käivita seda skripti oma hosti Pythoniga

### Sümptom: `relation "staging.user_status" does not exist`

Tõenäoline põhjus:

- tabelid ei ole veel loodud

Lahendus:

- ava `psql`
- käivita `\i /scripts/01_create_tables.sql`
- alles siis lae `CSV` ja käivita `ETL` skript

### Sümptom: `analytics.user_profile` jääb tühjaks või väljad on `NULL`

Tõenäoline põhjus:

- `CSV` faili pole staging-tabelisse laaditud või ühendusvõti ei klapi

Lahendus:

- kontrolli, et käivitasid faili `\i /scripts/02_load_user_status.sql`
- vaata skriptis `normalize_email`, mil viisil ühendusvõti puhastatakse

## Kokkuvõte

Selles praktikumis tegid läbi esimese töötava andmete integreerimise toru.

Töövoog oli järgmine:

1. lõid skeemad ja tabelid;
2. laadisid `CSV` faili staging-tabelisse;
3. lugesid kasutajad `API`-st;
4. puhastasid ühise võtme;
5. ühendasid `API` ja `CSV` andmed;
6. laadisid lõpptulemuse tabelisse.

See on lihtne, aga päris `ETL` näide. Suuremates süsteemides on samme rohkem, kuid põhiloogika on sama.

## Lisaülesanded

Need ülesanded ei pea mahtuma praktikumi põhiaja sisse.

### Lisaülesanne 1: lisa kolmas allikas ja täienda skripti

Selles ülesandes tood mängu ka faili [`data/teavituseelistused.json`](./data/teavituseelistused.json).

Tee nii:

1. valmista andmebaas ette:

```sql
\i /scripts/lisa_01_prepare_preferences.sql
```

2. tee mallist oma tööfail:

macOS-is, Linuxis ja Codespacesis:

```bash
cp scripts/lisa_03_integrate_users_template.py scripts/lisa_03_integrate_users.py
```

Windows PowerShellis:

```powershell
Copy-Item scripts/lisa_03_integrate_users_template.py scripts/lisa_03_integrate_users.py
```

3. täienda failis `scripts/lisa_03_integrate_users.py` märgitud funktsioonid
4. käivita uus skript Pythoni konteineri sees

Selles lisaülesandes teed ise sama töövoo järgmise sammu läbi: liigud kahelt allikalt kolme allikani.

Pärast oma katset võid võrrelda tulemust failiga:

- [`scripts/naidis_lahendused/lisa_03_integrate_users_lahendus.py`](./scripts/naidis_lahendused/lisa_03_integrate_users_lahendus.py)

### Lisaülesanne 2: lisa telefoninumber lõpptabelisse

Praegu ei vii põhiskript `API` vastusest telefoninumbrit lõpptabelisse.

Tee nii:

- lisa väli `phone` tabelisse `analytics.user_profile`;
- lisa telefoninumber skripti `fetch_api_users` tulemustesse;
- lae see ka lõpptabelisse.

### Lisaülesanne 3: märgista kasutajad, kelle kohta osa lisainfost puudub

See ülesanne eeldab, et oled teinud lisaülesande 1.

Loo lõpptabelisse väli `has_missing_additional_data`, mis on `true`, kui kasutaja kohta puudub kas staatus või teavituseelistus.

See ülesanne aitab märgata, millise kasutaja kohta ei ole kõiki täiendavaid andmeid kätte saadud.

### Lisaülesanne 4: tee lihtne kokkuvõttepäring

See ülesanne eeldab, et oled teinud lisaülesande 1.

Kirjuta `SQL` päring, mis näitab:

- mitu kasutajat on iga `account_status` väärtuse all;
- mitu kasutajat eelistab kanalit `email`, `sms` või `push`.

Võid teha selle otse `psql` sees või panna uude faili `scripts/05_summary_queries.sql`.

## Koristamine

Kui tahad praktikumi keskkonna lõpuks peatada:

```bash
docker compose down
```

Kui tahad alustada täiesti puhtalt, eemalda ka andmemahu sisu:

```bash
docker compose down -v
```

Kui tahad ainult praktikumi skeemad andmebaasist ära kustutada, aga konteineri alles jätta:

1. ava `psql`
2. käivita:

```sql
\i /scripts/99_reset.sql
```
