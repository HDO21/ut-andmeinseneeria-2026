# Praktikum 9: Ärianalüütika ja andmete serveerimine Supersetiga

## Sisukord

- [Praktikumi eesmärk](#praktikumi-eesmärk)
- [Õpiväljundid](#õpiväljundid)
- [Hinnanguline ajakulu](#hinnanguline-ajakulu)
- [Eeldused](#eeldused)
- [Enne alustamist](#enne-alustamist)
- [Praktikumi failid](#praktikumi-failid)
- [Miks see teema on oluline?](#miks-see-teema-on-oluline)
- [Uued mõisted](#uued-mõisted)
- [Soovitatud töötee](#soovitatud-töötee)
- [1. Ava praktikumi kaust](#1-ava-praktikumi-kaust)
- [2. Loo `.env` fail](#2-loo-env-fail)
- [3. Käivita keskkond](#3-käivita-keskkond)
- [4. Kontrolli, et tehniline taust töötab](#4-kontrolli-et-tehniline-taust-töötab)
- [5. Ava Superset ja starter-dashboard](#5-ava-superset-ja-starter-dashboard)
- [6. Vaata, kuidas andmete värskendus töötab](#6-vaata-kuidas-andmete-värskendus-töötab)
- [7. Loo joonis: päevane käive ajas](#7-loo-joonis-päevane-käive-ajas)
- [8. Loo joonis: kategooriate võrdlus](#8-loo-joonis-kategooriate-võrdlus)
- [9. Lisa joonised dashboardile](#9-lisa-joonised-dashboardile)
- [10. Lisa Markdown-plokk andmelooga](#10-lisa-markdown-plokk-andmelooga)
- [11. Lisa ajafilter](#11-lisa-ajafilter)
- [12. Sõnasta mõõdiku piirangud](#12-sõnasta-mõõdiku-piirangud)
- [Kontrollpunktid](#kontrollpunktid)
- [Levinud vead ja lahendused](#levinud-vead-ja-lahendused)
- [Kokkuvõte](#kokkuvõte)
- [Valikuline lisaharjutus](#valikuline-lisaharjutus)
- [Koristamine](#koristamine)

## Praktikumi eesmärk

Selle praktikumi eesmärk on koostada Apache Supersetis väike veebipoe müügi dashboard.

Tehniline taust käivitub `docker compose` abil. PostgreSQL hoiab andmeid, cron lisab iga minuti järel väikese mikrobatch'i uusi müügisündmusi ja Superset näitab tulemusi veebiliideses.

Praktikumi põhirõhk on Supersetis:

- vaatad valmis starter-dashboardi;
- jälgid, kuidas andmed taustal värskenevad;
- lood kaks uut joonist;
- lisad need dashboardile;
- kirjutad lühikese andmeloo, mis vastab äriküsimusele.

Äriküsimus on:

> Millised veebipoe müügitulemused vajavad juhtkonna tähelepanu?

## Õpiväljundid

Praktikumi lõpuks oskad:

- selgitada, mis vahe on andmetabelil, andmekogumil, joonisel ja dashboardil;
- avada Apache Superseti ja leida ettevalmistatud andmekogumid;
- lugeda dashboardilt andmete värskuse infot;
- luua Supersetis vähemalt kaks joonist;
- ühendada KPI, trendijoonis, võrdlusjoonis ja töövoo logi üheks dashboardiks;
- lisada dashboardile lühikese Markdown-teksti;
- sõnastada, mida valitud KPI näitab ja mida see ei näita.

## Hinnanguline ajakulu

Arvesta umbes 2 kuni 2,5 tunniga.

See aeg jaguneb ligikaudu nii:

- 20 min keskkonna käivitamiseks ja Superseti avamiseks;
- 20 min starter-dashboardi ja andmete värskenduse mõistmiseks;
- 35 min kahe joonise loomiseks;
- 25 min dashboardi kujundamiseks ja Markdown-ploki lisamiseks;
- 20 min mõõdikute piirangute ja järelduste sõnastamiseks;
- 10 min kokkuvõtteks ja koristamiseks.

## Eeldused

Sul on vaja:

- `VS Code`-i või GitHub Codespacesit;
- terminali;
- töötavat Dockeri keskkonda;
- selle repositooriumi faile.

Kasuks tuleb, kui varasematest baastaseme praktikumidest on tuttavad:

- õige praktikumi kausta avamine;
- `.env` faili loomine `.env.example` põhjal;
- `docker compose up -d --build`;
- `docker compose ps`;
- mõte, et andmetoru võib laadida ajalugu ja seejärel lisada uusi andmeid väikeste portsjonitena.

See praktikum seostub eriti kahe varasema teemaga:

- 4. praktikumis oli veebipoe näide ja cron-põhine töövoog;
- 8. praktikumis liikusid veebipoe müügisündmused taustatöö kaudu analüütika tabelitesse.

Selles praktikumis jätame järjekorra ja worker'i kõrvale. Kasutame mikrobatch'i, sest tahame keskenduda andmete visualiseerimisele.

## Enne alustamist

### Soovitatud keskkond

Selle praktikumi jaoks sobib hästi järgmine tööviis:

- ava kaust `09-arianalyytika-ja-serveerimine/baastase` `VS Code`-is;
- kasuta `VS Code`-i sisseehitatud terminali;
- hoia lahti `README.md` ja vajadusel `compose.yml`;
- tee tehnilised käsud hosti terminalis;
- tee dashboardi loomise sammud Superseti veebiliideses.

Host tähendab sinu arvutit või Codespace'i tööruumi. Konteiner tähendab Dockeri sees töötavat teenust.

### Teenused

Selles praktikumis käivitub viis põhilist teenust:

- `db` on PostgreSQL andmebaas;
- `bootstrap` loob algse müügiajaloo ja lõpetab töö;
- `scheduler` hoiab cron'i käimas ja lisab iga minuti järel uusi müügisündmusi;
- `superset-db` hoiab Superseti enda metaandmeid;
- `superset` on veebirakendus, kus lood joonised ja dashboardi.

Lisaks jooksevad korraks `superset-init` ja `superset-import`. Need seadistavad Superseti ja impordivad starter-dashboardi.

### Puhas algus

See praktikum kasutab vaikimisi porte:

- PostgreSQL hostis: `5439`;
- Superset hostis: `8088`.

Kui port `8088` on juba kasutusel, muuda `.env` failis väärtust:

```text
SUPERSET_PORT_HOST=8089
```

Kui oled praktikumit varem käivitanud ja tahad täiesti puhast algust, kasuta juhendi lõpus olevat `docker compose down -v` käsku.

## Praktikumi failid

Kõik allpool toodud suhtelised failiteed eeldavad, et asud kaustas `09-arianalyytika-ja-serveerimine/baastase`.

- [`compose.yml`](./compose.yml) kirjeldab andmebaasi, schedulerit ja Superseti teenuseid
- [`.env.example`](./.env.example) sisaldab vaikimisi keskkonnamuutujaid
- [`.gitignore`](./.gitignore) hoiab `.env` faili gitist väljas
- [`Dockerfile.scheduler`](./Dockerfile.scheduler) ehitab cron'i ja Pythoni skriptiga konteineri
- [`Dockerfile.superset`](./Dockerfile.superset) lisab Superseti konteinerisse PostgreSQL draiveri
- [`init/01_create_objects.sql`](./init/01_create_objects.sql) loob tabelid, vaated ja logitabeli
- [`source_data/products.csv`](./source_data/products.csv) sisaldab veebipoe tooteid
- [`source_data/stores.csv`](./source_data/stores.csv) sisaldab veebipoe poode
- [`scripts/microbatch.py`](./scripts/microbatch.py) loob algse ajaloo ja lisab uusi müügisündmusi
- [`scripts/01_check_data.sql`](./scripts/01_check_data.sql) sisaldab kontrollpäringuid
- [`scheduler/crontab`](./scheduler/crontab) käivitab mikrobatch'i iga minuti järel
- [`scheduler/entrypoint.sh`](./scheduler/entrypoint.sh) paneb cron'i tööle ja käivitab esimese mikrobatch'i kohe
- [`superset/dashboard_export`](./superset/dashboard_export) sisaldab starter-dashboardi impordifaile
- [`superset/zip_dashboard.py`](./superset/zip_dashboard.py) pakib starter-dashboardi Superseti imporditavaks ZIP-failiks
- [`viited.md`](./viited.md) sisaldab visualiseerimise ja andmeloo lisamaterjale

## Miks see teema on oluline?

Andmeinseneri töö ei lõpe sellega, et andmed on tabelis.

Kui andmeid kasutab juht, analüütik või valdkonna spetsialist, peab tulemus aitama otsustada. Selle jaoks on vaja:

- selgeid KPI-sid;
- arusaadavaid jooniseid;
- nähtavat andmete värskust;
- ausat piiri selle kohta, mida andmed näitavad ja mida mitte.

Näiteks kogukäive on kasulik mõõdik, aga ta ei vasta üksi küsimusele, kas müük on kasumlik. Käive võib kasvada ka siis, kui müüakse madalama marginaaliga tooteid või tehakse palju allahindlusi.

Selles praktikumis harjutame üleminekut tabelist andmelooni. Andmelugu ei tähenda ilukirjandust. See tähendab, et joonised vastavad konkreetsele küsimusele ja aitavad lugejal näha peamist mustrit.

## Uued mõisted

### KPI

Probleem on selles, et tabelis võib olla palju veerge, aga otsustamiseks on vaja mõnda selgelt defineeritud mõõdikut.

`KPI` tähendab inglise keeles `Key Performance Indicator`. Eesti keeles kasutame siin selgitust: võtmenäitaja.

Näide:

Kogukäive näitab, kui suure summa eest on veebipoes tellimusi tehtud.

Tehniliselt arvutame selle selles praktikumis nii:

```sql
SUM(quantity * unit_price_eur)
```

### Dashboard

Kui iga küsimuse jaoks peab uuesti SQL-i kirjutama, jõuab andmetest kasu aeglaselt kasutajani.

Dashboard ehk näidikulaud on mitme joonise ja mõõdiku koondvaade. Selle eesmärk on anda kiiresti vastus korduvatele küsimustele.

Näide:

Veebipoe dashboardil võib olla kogukäive, päevane müügitrend, kategooriate võrdlus ja andmete viimase laadimise aeg.

### Andmekogum

Superset ei loo joonist otse suvalisest failist. Ta vajab kirjeldatud andmeallikat.

Andmekogum ehk `Dataset` on Superseti kirje, mis viitab andmebaasi tabelile või vaatele.

Näide:

Andmekogum `analytics.v_sales_by_category` viitab andmebaasi vaatele, kus müük on koondatud kuupäeva ja kategooria järgi.

### Mikrobatch

Kõiki andmeid ei pea alati laadima ühe suure pakina. Samas ei pea baastaseme näites kohe kasutama keerukat sõnumijärjekorda.

Mikrobatch on väike ports andmeid, mida töödeldakse regulaarselt.

Näide:

Selles praktikumis lisab cron iga minuti järel 12 uut veebipoe müügisündmust.

### Andmeaken ja watermark

Kui andmed jõuavad süsteemi osade kaupa, tekib küsimus: millise ajavahemiku andmed jõudsid viimases laadimises kohale?

Andmeaken kirjeldab selle laadimise sündmuste ajavahemikku. `Watermark` on tehniline märk, mis näitab, kui kaugele töötlus andmeajas jõudis.

Näide:

Kui logis on `watermark_from = 2026-04-15 08:00` ja `watermark_to = 2026-04-15 08:55`, siis lisas viimane mikrobatch selle ajavahemiku sündmused.

### Andmelugu

Joonis üksi ei pruugi öelda, miks ta oluline on.

Andmelugu on lühike selgitus, mis seob joonise äriküsimusega.

Näide:

“Käive kasvab viimastel päevadel, kuid kasv tuleb peamiselt ühest kategooriast. Järgmiseks peaks kontrollima, kas kasv tuleb suuremast tellimuste arvust või kallimatest ostukorvidest.”

## Soovitatud töötee

Vaikimisi tee on:

1. Käivita kogu tehniline keskkond ühe käsuga.
2. Ava Superset.
3. Vaata starter-dashboardilt, et andmed ja töövoo logi uuenevad.
4. Loo kaks uut joonist.
5. Lisa joonised dashboardile.
6. Lisa Markdown-plokk, mis vastab äriküsimusele.

## 1. Ava praktikumi kaust

Tee see käsk hosti terminalis.

```bash
cd 09-arianalyytika-ja-serveerimine/baastase
```

Kui töötad GitHub Codespacesis, võib täielik tee olla:

```text
/workspaces/ut-andmeinseneeria-2026/09-arianalyytika-ja-serveerimine/baastase
```

## 2. Loo `.env` fail

Tee see käsk hosti terminalis.

```bash
cp .env.example .env
```

Kui töötad PowerShellis ja `cp` ei tööta, kasuta:

```powershell
Copy-Item .env.example .env
```

Vaikimisi väärtused sobivad praktikumi läbimiseks. Päris töös ei kasutataks selliseid lihtsaid paroole.

## 3. Käivita keskkond

Tee see käsk hosti terminalis.

```bash
docker compose up -d --build
```

See teeb mitu asja:

- ehitab scheduler'i ja Superseti konteinerid;
- loob PostgreSQL andmebaasi;
- loob tabelid ja vaated;
- laeb algse veebipoe müügiajaloo;
- käivitab cron'i, mis lisab uusi sündmusi;
- seadistab Superseti;
- impordib starter-dashboardi.

Esimene käivitus võib võtta mitu minutit. Superset on üsna suur rakendus.

## 4. Kontrolli, et tehniline taust töötab

Tee see käsk hosti terminalis.

```bash
docker compose ps
```

Oodatav tulemus:

- `db`, `scheduler`, `superset-db` ja `superset` on olekus `running` või `healthy`;
- `bootstrap`, `superset-init` ja `superset-import` on töö lõpetanud;
- `bootstrap`, `superset-init` ja `superset-import` võivad olla olekus `exited (0)`. See on korras, sest need on ühekordsed seadistustööd.

Kui tahad andmebaasi seisu käsurealt kontrollida, tee:

```bash
docker compose exec scheduler psql -h db -U praktikum -d praktikum -f scripts/01_check_data.sql
```

Oodatav tulemus:

- toodete ja poodide tabelis on read;
- `staging.order_events` sisaldab algset ajalugu;
- `monitoring.microbatch_run_log` sisaldab vähemalt `bootstrap` ja `scheduled` ridu.

## 5. Ava Superset ja starter-dashboard

Ava brauseris:

```text
http://localhost:8088
```

Kui muutsid `.env` failis `SUPERSET_PORT_HOST` väärtust, kasuta seda porti.

Logi sisse:

```text
kasutaja: admin
parool: admin
```

Leia ülemisest menüüst **Dashboards** ja ava:

```text
Veebipoe müügi ülevaade
```

Starter-dashboardil peaks olema:

- KPI `Kogukäive`;
- tabel `Viimased laadimised`.

Need kaks plokki on meelega lihtsad. Nende eesmärk on kinnitada, et andmed ja Superset töötavad.

## 6. Vaata, kuidas andmete värskendus töötab

Starter-dashboardil on automaatne värskendus seatud 30 sekundi peale.

Vaata tabelit `Viimased laadimised`.

Oodatav tulemus:

- iga umbes minuti järel ilmub uus `scheduled` rida;
- `rows_inserted` näitab, mitu müügisündmust lisati;
- `watermark_from` ja `watermark_to` näitavad, millise andmeaja sündmused jõudsid viimasesse laadimisse;
- KPI `Kogukäive` kasvab aja jooksul.

Kui tabel ei muutu kohe, oota kuni järgmise täisminutini. Cron käivitub minuti kaupa.

## 7. Loo joonis: päevane käive ajas

Nüüd lood esimese uue joonise. See vastab küsimusele:

> Kuidas müük ajas muutub?

Tee sammud Superseti veebiliideses.

1. Ava **Charts**.
2. Vajuta **+ Chart**.
3. Vali dataset:

```text
v_sales_daily
```

4. Vali visualiseerimistüüp:

```text
Line Chart
```

5. Vajuta **Create new chart**.
6. Seadista joonis:

| Väli | Väärtus |
|------|---------|
| X-axis | `sales_date` |
| Metrics | `SUM(gross_sales_eur)` |
| Dimensions või Series | `region` |
| Time range | `No filter` |

7. Vajuta **Run**.
8. Salvesta joonis nimega:

```text
Päevane käive piirkonniti
```

Oodatav tulemus:

Näed joondiagrammi, kus käive muutub päevade kaupa ja jooned eristavad piirkondi.

Kui joonisel on liiga palju müra, eemalda `region` ja vaata ainult kogu päevast käivet.

## 8. Loo joonis: kategooriate võrdlus

Teine joonis vastab küsimusele:

> Millised tootekategooriad annavad kõige rohkem käivet?

Tee sammud Superseti veebiliideses.

1. Ava **Charts**.
2. Vajuta **+ Chart**.
3. Vali dataset:

```text
v_sales_by_category
```

4. Vali visualiseerimistüüp:

```text
Bar Chart
```

5. Vajuta **Create new chart**.
6. Seadista joonis:

| Väli | Väärtus |
|------|---------|
| X-axis | `category` |
| Metrics | `SUM(gross_sales_eur)` |
| Sort by | `SUM(gross_sales_eur)` |
| Sort descending | sees |
| Time range | `No filter` |

7. Vajuta **Run**.
8. Salvesta joonis nimega:

```text
Käive kategooriate kaupa
```

Oodatav tulemus:

Näed tulpdiagrammi, kus kategooriad on käibe järgi võrreldavad.

## 9. Lisa joonised dashboardile

Tee sammud Superseti veebiliideses.

1. Ava **Dashboards**.
2. Ava dashboard:

```text
Veebipoe müügi ülevaade
```

3. Vajuta **Edit dashboard**.
4. Lisa loodud joonised:

- `Päevane käive piirkonniti`;
- `Käive kategooriate kaupa`.

5. Paiguta KPI ja logi ülemisele reale.
6. Paiguta trendijoonis ja kategooriajoonis järgmisele reale.
7. Salvesta muudatused.

Hea dashboard aitab silmal liikuda üldiselt detailsemale:

- kõigepealt KPI;
- siis trend ajas;
- siis võrdlus kategooriate või piirkondade vahel;
- lõpuks andmete värskuse logi.

## 10. Lisa Markdown-plokk andmelooga

Nüüd lisa dashboardile lühike tekstiplokk. See aitab joonised äriküsimusega siduda.

Tee sammud Superseti veebiliideses.

1. Ava sama dashboard redigeerimisvaates.
2. Lisa **Markdown** plokk.
3. Kirjuta sinna lühike tekst.

Võid kasutada seda malli:

```markdown
### Mida juhtkond peaks märkama?

- Peamine muutus:
- Kõige tugevam kategooria või piirkond:
- Võimalik järgmine küsimus:
- Piirang: need andmed näitavad käivet, mitte kasumit.
```

Ära kirjuta kõike, mida joonised näitavad. Kirjuta see, mis aitab äriküsimusele vastata.

## 11. Lisa ajafilter

Ajafilter aitab kasutajal vaadata sama dashboardi eri ajavahemikes.

Tee sammud Superseti veebiliideses.

1. Ava dashboard redigeerimisvaates.
2. Ava filtrite seadistus.
3. Lisa filter tüübiga **Time range** või **Date range**.
4. Seo filter veeruga:

```text
sales_date
```

5. Rakenda filter loodud müügijoonistele.
6. Salvesta dashboard.

Oodatav tulemus:

Dashboardi kasutaja saab valida ajavahemiku ja vaadata, kuidas trend ning kategooriate võrdlus muutuvad.

Kui filter ei rakendu kõigile joonistele, kontrolli, kas joonised kasutavad datasette, kus on olemas veerg `sales_date`.

## 12. Sõnasta mõõdiku piirangud

Vali üks mõõdik, näiteks `Kogukäive`, ja vasta lühidalt kolmele küsimusele.

Kirjuta vastus kas Markdown-plokki või eraldi märkmetesse.

| Küsimus | Näidisvastus |
|---------|--------------|
| Mida mõõdik mõõdab? | Tellimuste kogusummat eurodes. |
| Kuidas mõõdik arvutatakse? | `SUM(quantity * unit_price_eur)`. |
| Mida mõõdik ei näita? | Kasumit, tagastusi, allahindlusi ega kliendirahulolu. |

See samm on oluline. Dashboard ilma mõõdiku piiranguta võib jätta vale kindlustunde.

## Kontrollpunktid

Praktikumi lõpus peaks sul olema:

- töötav Superset aadressil `http://localhost:8088`;
- dashboard `Veebipoe müügi ülevaade`;
- KPI `Kogukäive`;
- logitabel `Viimased laadimised`;
- sinu loodud trendijoonis;
- sinu loodud kategooria või piirkonna võrdlusjoonis;
- Markdown-plokk, mis sõnastab peamise tähelepaneku ja vähemalt ühe piirangu;
- nähtav andmete värskendus cron'i logi kaudu.

## Levinud vead ja lahendused

### `docker compose` ütleb, et port on juba kasutusel

Sümptom:

```text
Bind for 0.0.0.0:8088 failed: port is already allocated
```

Tõenäoline põhjus:

Mõni teine Superset või veebiteenus kasutab porti `8088`.

Lahendus:

Muuda `.env` failis porti:

```text
SUPERSET_PORT_HOST=8089
```

Seejärel käivita:

```bash
docker compose up -d
```

### Superset avaneb, aga dashboardi ei ole

Sümptom:

Superset töötab, kuid `Veebipoe müügi ülevaade` puudub.

Tõenäoline põhjus:

`superset-import` teenus ei lõpetanud edukalt.

Lahendus:

Vaata importija logi:

```bash
docker compose logs superset-import
```

Kui seal on andmebaasiühenduse viga, kontrolli, kas `.env` failis olevad PostgreSQL väärtused on samad, millega stack käivitati.

### Dashboard ei värskene

Sümptom:

`Viimased laadimised` tabel ei saa uusi ridu.

Tõenäoline põhjus:

`scheduler` ei tööta või cron ei käivitu.

Lahendus:

Kontrolli teenuseid:

```bash
docker compose ps
```

Vaata scheduler'i logi:

```bash
docker compose logs scheduler
```

Vaata ka hosti logifaili:

```bash
tail -n 30 logs/pipeline.log
```

### Joonis ei näita andmeid

Sümptom:

Supersetis on tühi joonis.

Tõenäoline põhjus:

Ajafilter on liiga kitsas või `Time range` ei ole `No filter`.

Lahendus:

Chart'i loomise vaates sea `Time range` väärtuseks:

```text
No filter
```

Seejärel vajuta **Run**.

### `psql` küsib parooli

Sümptom:

Käsk küsib parooli või annab autentimise vea.

Tõenäoline põhjus:

Käsk ei kasuta konteineri keskkonnamuutujaid või `.env` väärtused on muudetud.

Lahendus:

Kasuta juhendis antud käsku scheduler'i konteineri kaudu:

```bash
docker compose exec scheduler psql -h db -U praktikum -d praktikum -f scripts/01_check_data.sql
```

Kui muutsid `.env` failis kasutajanime, parooli või andmebaasi nime, kohanda ka käsku.

## Kokkuvõte

Selles praktikumis ehitasid Supersetis väikese veebipoe dashboardi.

Tehniline taust tegi kolm asja:

- lõi sünteetilise müügiajaloo;
- lisas cron'i abil uusi müügisündmusi;
- tegi andmete värskuse logi Supersetis nähtavaks.

Sisuline töö oli dashboardi koostamine:

- KPI annab kiire üldpildi;
- trendijoonis näitab muutust ajas;
- võrdlusjoonis aitab leida kategooria või piirkonna erinevusi;
- Markdown-plokk aitab liikuda kirjeldavast vaatest seletava andmelooni.

Hea dashboard ei ole ainult piltide kogum. See on korrastatud vastus äriküsimusele.

## Valikuline lisaharjutus

Vali üks lisaülesanne.

1. Lisa kolmas joonis piirkondade võrdluseks datasetist `v_sales_by_region`.
2. Lisa teine KPI: keskmine ostukorv datasetist `v_dashboard_kpi`.
3. Muuda Markdown-plokk konkreetsemaks: kirjuta üks soovitus ja üks kontrollküsimus.
4. Ava **SQL Lab** ja uuri päringuga, milline kategooria annab suurima käibe.

Näidispäring SQL Labis:

```sql
SELECT
    category,
    SUM(gross_sales_eur) AS revenue_eur
FROM analytics.v_sales_by_category
GROUP BY category
ORDER BY revenue_eur DESC;
```

## Koristamine

Kui tahad teenused peatada, aga andmed alles jätta, kasuta hosti terminalis:

```bash
docker compose down
```

Kui tahad kustutada ka andmebaasi ja Superseti salvestatud dashboardid, kasuta:

```bash
docker compose down -v
```

Järgmisel käivitamisel luuakse kõik uuesti.
