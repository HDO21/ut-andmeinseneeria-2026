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

Selle praktikumi eesmärk on koostada Apache Supersetis väike veebipoe müügi dashboard ehk näidikulaud.

Juhendis kasutame Superseti veebiliidese järgi sõna `dashboard`, sest sama sõna näed ka menüüdes.

Tehniline taust käivitub `docker compose` abil. Kohalik `source-api` simuleerib veebipoe müügisündmuste allikat, PostgreSQL hoiab andmeid, `cron` ehk ajastaja laadib iga minuti järel väikese andmeportsjoni ehk mikrobatch'i ja Superset näitab tulemusi veebiliideses.

Praktikumi põhirõhk on Supersetis:

- vaatad valmis starter-dashboardi;
- jälgid, kuidas andmed taustal värskenevad;
- lood kaks uut joonist;
- lisad need dashboardile;
- kirjutad lühikese andmeloo, mis vastab äriküsimusele.

Äriküsimus on:

> Millistes tootekategooriates ja piirkondades peaks juhtkond valitud perioodi müügitulemusi lähemalt uurima?

## Õpiväljundid

Praktikumi lõpuks oskad:

- selgitada, mis vahe on andmetabelil, andmekogumil, joonisel ja dashboardil;
- avada Apache Superseti ja leida ettevalmistatud andmekogumid;
- lugeda dashboardilt andmete värskuse infot;
- luua Supersetis vähemalt kaks joonist;
- ühendada KPI ehk võtmenäitaja, trendijoonis, võrdlusjoonis ja töövoo logi üheks dashboardiks;
- lisada dashboardile lühikese Markdown-teksti ehk vormindatava tekstiploki;
- sõnastada, mida valitud võtmenäitaja näitab ja mida see ei näita.

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

Kui kasutad Windowsit, vali üks terminal ja püsi selles kogu praktikumi vältel.
Soovitatud valik on `PowerShell` või `Git Bash`. Juhendis on eraldi märgitud
need kohad, kus PowerShelli käsk erineb Linuxi või macOS-i käsust.

Windowsis peab Docker Desktop enne `docker compose` käske töötama. Ava Docker
Desktop ja oota, kuni selle olek näitab, et Docker Engine on käivitunud. Kui
repo asub OneDrive'i või muu sünkroonitud kausta all ja Docker ei suuda faile
konteinerisse jagada, tõsta repo tavalisse töökausta, näiteks `C:\projects`.

Sa ei pea Windowsis käsitsi käivitama ühtegi `.sh` faili. Need failid töötavad
Linuxi konteineri sees ja Docker käivitab need ise.

Kui kasutad GitHub Codespacesit, ava Superset brauseris Codespacesi **Ports**
vaate kaudu. Aadress võib siis olla teistsugune kui `localhost`, kuid port on
ikka sama, näiteks `8088`.

Codespacesis töötab Superset samade konteineritega, kui selles Codespace'is on
Docker ja `docker compose` olemas. Portide avamine käib seal veidi teisiti:
jäta port `8088` **Private** nähtavusega. Ära tee seda praktikumi ajal
avalikuks pordiks. Kui pead Superseti linki kellegi teisega jagama, muuda enne
esimest käivitust `.env` failis vähemalt `SUPERSET_ADMIN_PASSWORD` ja
`SUPERSET_SECRET_KEY`.

### Teenused

Selles praktikumis käivitub viis põhilist teenust:

- `db` on PostgreSQL andmebaas;
- `source-api` on kohalik veebipoe sündmuste allikas;
- `bootstrap` loob algse müügiajaloo ja lõpetab töö;
- `scheduler` hoiab cron'i käimas ja laadib source API-st iga minuti järel järgmise mikrobatch'i;
- `superset` on veebirakendus, kus lood joonised ja dashboardi.

Superseti metaandmed hoitakse samas `db` konteineris ja samas `praktikum` andmebaasis. Need tekivad PostgreSQL-i `public` skeemi. Praktikumi müügi- ja logiandmed on eraldi skeemides `staging`, `intermediate`, `analytics`, `monitoring` ja `control`. Nii on sul lihtsam eristada Superseti sisetabeleid ja praktikumi andmeid.

Lisaks jooksevad korraks `superset-init` ja `superset-import`. Need seadistavad Superseti ja impordivad starter-dashboardi.

### Puhas algus

See praktikum kasutab vaikimisi porte:

- PostgreSQL hostis: `5439`;
- source API hostis: `8019`;
- Superset hostis: `8088`.

Praktikumi ajavöönd on `.env` failis:

```text
TZ=Europe/Tallinn
```

See hoiab source API sündmuste aja, cron'i logi, andmebaasi päringud ja
Superseti vaated samas kohalikus ajas. Praktikumi ajal ära seda väärtust muuda.

Kui port `8088` on juba kasutusel, muuda `.env` failis väärtust:

```text
SUPERSET_PORT_HOST=8089
```

Kui port `8019` on juba kasutusel, muuda samas failis väärtust:

```text
SOURCE_API_PORT_HOST=8020
```

Vaikimisi andmeaken on seatud 14.05.2026 praktikumi järgi. Source API alustab
kuupäevast `2026-04-30` ja alglaadimine võtab 14 päeva ajalugu. See tähendab,
et starter-dashboardil on kohe näha vahemik 30.04-13.05.

Source API ei anna välja tulevikusündmusi. Kui 14.05 sündmuse kellaaeg ei ole
veel kätte jõudnud, võib scheduler kirjutada logisse `skipped` rea. See ei ole
viga. See tähendab, et töövoog küsis uusi andmeid, aga allikas ei saanud veel
järgmist müügisündmust anda.

Kui oled praktikumit varem käivitanud ja tahad täiesti puhast algust, kasuta juhendi lõpus olevat `docker compose down -v` käsku.

## Praktikumi failid

Kõik allpool toodud suhtelised failiteed eeldavad, et asud kaustas `09-arianalyytika-ja-serveerimine/baastase`.

- [`compose.yml`](./compose.yml) kirjeldab andmebaasi, schedulerit ja Superseti teenuseid
- [`.env.example`](./.env.example) sisaldab vaikimisi keskkonnamuutujaid
- [`.gitignore`](./.gitignore) hoiab `.env` faili gitist väljas
- [`Dockerfile.scheduler`](./Dockerfile.scheduler) ehitab cron'i ja Pythoni skriptiga konteineri
- [`Dockerfile.superset`](./Dockerfile.superset) lisab Superseti konteinerisse PostgreSQL draiveri
- [`init/01_create_objects.sql`](./init/01_create_objects.sql) loob tabelid, vaated ja logitabeli
- [`source_api/server.py`](./source_api/server.py) käivitab kohaliku veebipoe sündmuste API
- [`source_data/products.csv`](./source_data/products.csv) sisaldab veebipoe tooteid
- [`source_data/stores.csv`](./source_data/stores.csv) sisaldab veebipoe poode
- [`scripts/microbatch.py`](./scripts/microbatch.py) toob source API-st sündmused ja laadib need andmebaasi
- [`scripts/01_check_data.sql`](./scripts/01_check_data.sql) sisaldab kontrollpäringuid
- [`scheduler/crontab`](./scheduler/crontab) käivitab mikrobatch'i iga minuti järel
- [`scheduler/entrypoint.sh`](./scheduler/entrypoint.sh) paneb cron'i tööle ja käivitab esimese mikrobatch'i kohe
- [`superset/dashboard_export`](./superset/dashboard_export) sisaldab starter-dashboardi impordifaile
- [`superset/zip_dashboard.py`](./superset/zip_dashboard.py) pakib starter-dashboardi Superseti imporditavaks ZIP-failiks
- [`viited.md`](./viited.md) sisaldab visualiseerimise ja andmeloo lisamaterjale

## Miks see teema on oluline?

Andmeinseneri töö ei lõpe sellega, et andmed on tabelis.

Kui andmeid kasutab juht, analüütik või valdkonna spetsialist, peab tulemus aitama otsustada. Selle jaoks on vaja:

- selgeid võtmenäitajaid ehk KPI-sid;
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

Selles praktikumis küsib cron iga minuti järel source API-st kuni 12 järgmist veebipoe müügisündmust. See piir ei ütle, mitu sündmust allikas tekkis. See ütleb, mitu sündmust ETL ühe käivitusega vastu võtab.

Kui allikas on rohkem kui 12 uut sündmust, jäävad ülejäänud järgmise käivituse ootele. See on tavaline mikrobatch-muster: laadijal on partii suurus, allikal võib olla sellest suurem maht.

Source API annab ainult need sündmused, mille sündmuse aeg on praktikumi
kohaliku aja järgi kätte jõudnud. Nii ei ilmu dashboardile tellimusi, mis
peaksid toimuma alles hiljem.

See on mikrobatch'i õppemudel, mitte tootmisvalmis voogedastusplatvorm. Tööelus võib sama rolli täita Kafka offset, CDC logipositsioon, Airflow metadata, Kubernetes CronJob või mõni muu orkestreerija. Siin hoiame mustri väikese ja nähtavana: source API annab järjestatud sündmused, `scheduler` loeb neid portsjonite kaupa ja `control.pipeline_state` jätab meelde järgmise sündmuse järjekorranumbri.

### Andmeaken ja watermark

Kui andmed jõuavad süsteemi osade kaupa, tekib küsimus: millise ajavahemiku andmed jõudsid viimases laadimises kohale?

Andmeaken kirjeldab selle laadimise sündmuste ajavahemikku. `Watermark` on tehniline märk, mis näitab, kui kaugele töötlus andmeajas jõudis.

Näide:

Kui logis on `watermark_from = 2026-05-14 13:00` ja `watermark_to = 2026-05-14 14:55`, siis lisas viimane mikrobatch selle ajavahemiku sündmused.

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

Kui kasutad Windows PowerShelli, töötab sama käsk samal kujul.

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

Vaikimisi väärtused sobivad praktikumi läbimiseks oma arvutis või privaatses
Codespace'is. `.env` fail jääb gitist välja.

Kui kasutad Codespacesit ja muudad porti `8088` avalikuks või jagad Superseti
linki teistega, muuda enne käivitamist vähemalt need read:

```text
SUPERSET_SECRET_KEY=kirjuta-siia-pikem-juhuslik-saladus
SUPERSET_ADMIN_PASSWORD=kirjuta-siia-uus-parool
```

Kui stack on juba varem käivitatud, ei pruugi Superset olemasoleva admini
parooli automaatselt üle kirjutada. Õppekeskkonnas on siis kõige lihtsam teha
puhas algus juhendi lõpus oleva `docker compose down -v` käsuga.

## 3. Käivita keskkond

Tee see käsk hosti terminalis.

```bash
docker compose up -d --build
```

Sama käsk töötab macOS-is, Linuxis, Git Bashis, Windows PowerShellis ja GitHub Codespacesis, kui Docker töötab.

See teeb mitu asja:

- ehitab scheduler'i ja Superseti konteinerid;
- loob PostgreSQL andmebaasi;
- loob tabelid ja vaated;
- laeb algse veebipoe müügiajaloo;
- käivitab cron'i, mis laadib source API-st järgmisi sündmusi;
- seadistab Superseti;
- impordib starter-dashboardi.

Esimene käivitus võib võtta mitu minutit, sest Superseti konteiner ehitatakse ja käivitatakse esimest korda.

## 4. Kontrolli, et tehniline taust töötab

Tee see käsk hosti terminalis.

```bash
docker compose ps
```

Oodatav tulemus:

- `db`, `source-api`, `scheduler` ja `superset` on olekus `running` või `healthy`;
- `bootstrap`, `superset-init` ja `superset-import` on töö lõpetanud;
- `bootstrap`, `superset-init` ja `superset-import` võivad olla olekus `exited (0)`. See on korras, sest need on ühekordsed seadistustööd.

`superset` käivitub alles pärast `superset-import` edukat lõppu. Kui Superset ei avane või dashboardi ei ole, vaata kõigepealt `superset-import` logi:

```bash
docker compose logs superset-import
```

Kui tahad andmebaasi seisu käsurealt kontrollida, tee:

```bash
docker compose exec scheduler psql -h db -U praktikum -d praktikum -f scripts/01_check_data.sql
```

Oodatav tulemus:

- `SHOW timezone` näitab `Europe/Tallinn`;
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
parool: praktikum09
```

Kui muutsid `.env` failis `SUPERSET_ADMIN_PASSWORD` väärtust, kasuta enda
määratud parooli.

Leia ülemisest menüüst **Dashboards** ja ava:

```text
Veebipoe müügi ülevaade
```

Starter-dashboardil peaks olema:

- KPI `Kogukäive`;
- tabel `Viimased laadimised`.

Starter-dashboardis on esialgu ainult kaks plokki. Need kinnitavad, et andmed ja Superset töötavad.

## 6. Vaata, kuidas andmete värskendus töötab

Starter-dashboardil on automaatne värskendus seatud 30 sekundi peale.

Vaata tabelit `Viimased laadimised`.

Oodatav tulemus:

- iga umbes minuti järel ilmub uus `scheduled` käivituse rida;
- `rows_inserted` näitab, mitu müügisündmust selles mikrobatch'is andmebaasi laaditi;
- `Andmeaken` näitab lühidalt, millise andmeaja sündmused jõudsid viimasesse laadimisse;
- KPI `Kogukäive` kasvab siis, kui source API-l on kätte jõudnud uusi sündmusi.

Kui tabelisse ilmub `skipped` rida, töötab scheduler õigesti, kuid allikal ei
ole veel uut kättesaadavat müügisündmust. Kui tabel ei muutu kohe, oota kuni
järgmise täisminutini. Cron käivitub minuti kaupa.

Soovi korral võid source API hetkeseisu vaadata brauseris:

```text
http://localhost:8019/docs
```

Codespacesis ava port `8019` **Ports** vaate kaudu.

## 7. Loo joonis: päevane käive ajas

Nüüd lood esimese uue joonise. See vastab küsimusele:

> Kuidas müük ajas muutub?

Superset võib veeruvalikus näidata kas tehnilist andmebaasinime või eestikeelset
pealkirja. Mõlemad viitavad samale veerule.

| Andmebaasi veerg | Superseti pealkiri |
|------------------|--------------------|
| `sales_date` | `Müügikuupäev` |
| `gross_sales_eur` | `Käive` |
| `region` | `Piirkond` |
| `category` | `Kategooria` |
| `order_count` | `Tellimuste arv` |
| `avg_order_eur` | `Keskmine ostukorv` |

SQL-is kasutatakse vasakpoolseid nimesid. Superseti rippmenüüs võid näha
parempoolseid pealkirju.

Tee sammud Superseti veebiliideses.

1. Ava **Charts**.
2. Vajuta **+ Chart**.
3. Vali dataset ehk Superseti andmekogum:

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
| X-axis | `sales_date` ehk `Müügikuupäev` |
| Metrics | `SUM(gross_sales_eur)` ehk `SUM(Käive)` |
| Dimensions või Series | `region` ehk `Piirkond` |
| Time range | `No filter` |

`Time range = No filter` tähendab siin, et joonisel endal ei ole püsivat
ajapiiri. Hiljem lisatav dashboardi ajafilter saab seda joonist juhtida
andmekogumi `sales_date` veeru kaudu.

Kui Superset ei paku valmis mõõdikut `SUM(gross_sales_eur)`, loo see samal
Metrics väljal: vali veerg `gross_sales_eur` ehk `Käive` ja koondamisviisiks
`SUM`.

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
| X-axis | `category` ehk `Kategooria` |
| Metrics | `SUM(gross_sales_eur)` ehk `SUM(Käive)` |
| Sort by | sama mõõdik: `SUM(gross_sales_eur)` ehk `SUM(Käive)` |
| Sort descending | sees |
| Time range | `No filter` |

Jäta ka siin `Time range` väärtuseks `No filter`, et dashboardi ühine ajafilter
saaks seda joonist hiljem muuta.

Kui Superset kuvab veerud eesti keeles, vali `Kategooria` ja `Käive`. Kui ta
kuvab tehnilised nimed, vali `category` ja `gross_sales_eur`.

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

Markdown on tekstivorming, kus pealkirjad ja loendid kirjutatakse otse teksti sisse. Superset oskab selle tekstina sisestatud ploki dashboardil vormindatult näidata.

Tee sammud Superseti veebiliideses.

1. Ava sama dashboard redigeerimisvaates.
2. Lisa **Markdown** plokk.
3. Kirjuta sinna lühike tekst.

Võid kasutada seda malli:

```markdown
### Mida juhtkond peaks lähemalt uurima?

- Peamine muutus:
- Kõige tugevam kategooria või piirkond:
- Võimalik järgmine küsimus:
- Piirang: need andmed näitavad käivet, mitte kasumit.
```

Ära kirjuta kõike, mida joonised näitavad. Kirjuta see, mis aitab äriküsimusele vastata.

## 11. Lisa ajafilter

Ajafilter aitab sama dashboardi eri ajavahemikes vaadata.

Tee sammud Superseti veebiliideses.

1. Ava dashboard redigeerimisvaates.
2. Ava filtrite seadistus.
3. Lisa filter tüübiga **Time range** või **Date range**.
4. Pane filtri nimeks:

```text
Müügikuupäev
```

5. Ava filtri ulatus ehk **Scoping** või **Apply to panels**.
6. Rakenda filter KPI-le `Kogukäive` ja loodud müügijoonistele.
7. Ära rakenda seda filtrit logitabelile `Viimased laadimised`.
   Logitabel näitab töövoo käivitusaega, mitte müügikuupäeva.
8. Salvesta filter ja seejärel dashboard.

`Time range` filter ei küsi tavaliselt eraldi veergu. Ta kasutab iga charti
enda ajaveergu. Praktikumi müügi-datasetites on selleks `sales_date`, mida
Superset võib näidata pealkirjaga `Müügikuupäev`.

Nende plokkide oluline ajaveerg on:

| Dashboardi plokk | Dataset | Ajaveerg |
|------------------|---------|----------|
| `Kogukäive` | `v_dashboard_kpi` | `sales_date` ehk `Müügikuupäev` |
| `Päevane käive piirkonniti` | `v_sales_daily` | `sales_date` ehk `Müügikuupäev` |
| `Käive kategooriate kaupa` | `v_sales_by_category` | `sales_date` ehk `Müügikuupäev` |
| `Viimased laadimised` | `v_recent_microbatch_runs` | `finished_at` ehk `Lõppes` |

Ära seo seda filtrit datasetiga `v_recent_microbatch_runs`. Selle logitabeli
ajaveerud on `finished_at`, `started_at`, `watermark_from` ja `watermark_to`,
aga need ei tähenda sama asja kui müügikuupäev.

Oodatav tulemus:

Saad valida ajavahemiku ja vaadata, kuidas KPI, trend ning kategooriate võrdlus muutuvad.
Katseta filtrit enne järgmise sammu juurde liikumist.

1. Vali filtris mõni lühem vahemik, näiteks `2026-04-30` kuni `2026-05-06`.
2. Kontrolli, et muutuvad `Kogukäive`, päevane trend ja kategooriate joonis.
3. Kontrolli, et `Viimased laadimised` ei muutu sama filtri tõttu.
4. Pane filter tagasi laiema vahemiku peale või eemalda filter.

Kui filter ei rakendu kõigile joonistele, kontrolli, kas joonised kasutavad datasette, kus on olemas veerg `sales_date`.
Superset võib sama veergu näidata nimega `Müügikuupäev`.

Kui KPI ei muutu, ava filtri seadistus uuesti ja kontrolli, et `Kogukäive KPI`
on filtri ulatuses. Kui muutsid praktikumi faile pärast esimest käivitust,
tee puhas algus, sest Superseti varasem metaandmete maht võib hoida vana
dashboardi seadistust.

```bash
docker compose down -v
docker compose up -d --build
```

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
- ajafilter, mis muudab müügijooniseid, kuid ei muuda töövoo logi;
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

### Codespacesis puudub `docker` käsk

Sümptom:

```text
docker: command not found
```

või:

```text
Cannot connect to the Docker daemon
```

Tõenäoline põhjus:

Codespace'i tööruumis ei ole Dockerit või ei ole see terminalist kasutatav.
Superset ise ei vaja Codespacesis erilahendust, aga selle praktikumi stack
käivitub Docker Compose'iga.

Lahendus:

Kasuta Codespace'i seadistust, kus Docker ja `docker compose` on lubatud, või
tööta lokaalselt Docker Desktopiga. Kui kasutad juhendaja antud Codespacesi
malli, loo Codespace vajaduse korral uuesti või tee pärast seadistuse muutmist
rebuild.

### Windowsis ei saa Dockeriga ühendust

Sümptom:

```text
Cannot connect to the Docker daemon
```

või:

```text
error during connect
```

Tõenäoline põhjus:

Docker Desktop ei tööta veel või Windows ei ole Dockeri Linuxi mootorit valmis
käivitanud.

Lahendus:

Ava Docker Desktop, oota kuni see on täielikult käivitunud, ja proovi sama
`docker compose` käsku uuesti. Kui viga kordub, taaskäivita Docker Desktop.

### Superset avaneb, aga dashboardi ei ole

Sümptom:

Superset töötab, kuid `Veebipoe müügi ülevaade` puudub.

Tõenäoline põhjus:

`superset-import` teenus ei lõpetanud edukalt või käivitati varem vana tühja Superseti andmemahu pealt.

Lahendus:

Vaata importija logi:

```bash
docker compose logs superset-import
```

Kui seal on andmebaasiühenduse viga, kontrolli, kas `.env` failis olevad PostgreSQL väärtused on samad, millega stack käivitati.

Kui oled selle praktikumi stacki juba varem käivitanud, tee puhas algus:

```bash
docker compose down -v
docker compose up -d --build
```

### `superset-import` lõpeb veaga

Sümptom:

```text
Container praktikum-supersetimport-09-base Error
service "superset-import" didn't complete successfully: exit 1
```

Tõenäoline põhjus:

Superseti starter-dashboardi import ei õnnestunud. Docker näitab siin ainult
üldist veateadet. Täpsem põhjus on `superset-import` konteineri logis.

Lahendus:

Vaata importija logi:

```bash
docker compose logs --no-color superset-import
```

Kui oled praktikumi faile muutnud või uuendanud, eemalda ebaõnnestunud
importija konteiner ja käivita Superset uuesti:

```bash
docker compose rm -f superset-import superset
docker compose up -d --build superset
```

Kui viga kordub ja tahad alustada täiesti puhtalt, kasuta:

```bash
docker compose down -v
docker compose up -d --build
```

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

Kui töötad Windows PowerShellis ja `tail` ei tööta, kasuta:

```powershell
Get-Content logs/pipeline.log -Tail 30
```

Kui logitabelis tekivad `skipped` read, ei ole see sama viga. `skipped`
tähendab, et source API-l ei olnud veel ühtegi uut sündmust, mille aeg oleks
kätte jõudnud.

### Scheduler ei käivitu Windowsis pärast faili muutmist

Sümptom:

```text
/entrypoint.sh: not found
```

või:

```text
bad interpreter
```

Tõenäoline põhjus:

Shelli skript või `scheduler/crontab` salvestati Windowsi `CRLF`
reavahetustega. Linuxi konteiner ootab `LF` reavahetusi.

Lahendus:

Ava `scheduler/entrypoint.sh` ja `scheduler/crontab` VS Code'is. Akna alumises
paremas servas vali reavahetuseks `LF` ja salvesta failid. Seejärel käivita
stack uuesti:

```bash
docker compose up -d --build
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
- laadis cron'i abil source API-st uusi müügisündmusi;
- tegi andmete värskuse logi Supersetis nähtavaks.

Sisuline töö oli dashboardi koostamine:

- KPI annab kiire üldpildi;
- trendijoonis näitab muutust ajas;
- võrdlusjoonis aitab leida kategooria või piirkonna erinevusi;
- Markdown-plokk aitab liikuda kirjeldavast vaatest seletava andmelooni.

Hea dashboard ei ole ainult piltide kogum. See on korrastatud vastus äriküsimusele.

## Valikuline lisaharjutus

Vali üks lisaülesanne.

1. Lisa dashboardile väike tabel, mis näitab valitud müügiperioodi algus- ja lõppkuupäeva.
2. Lisa kolmas joonis piirkondade võrdluseks datasetist `v_sales_by_region`.
3. Lisa teine KPI: keskmine ostukorv datasetist `v_dashboard_kpi`.
   Kasuta arvutust `SUM(total_revenue_eur) / SUM(total_orders)`, et ajafiltri
   korral oleks tulemus kogu valitud perioodi keskmine.
4. Muuda Markdown-plokk konkreetsemaks: kirjuta üks soovitus ja üks kontrollküsimus.
5. Ava **SQL Lab** ja uuri päringuga, milline kategooria annab suurima käibe.

### Lisaülesanne: näita valitud müügiperioodi

Ajafilter on dashboardi ülaservas näha, aga vahel on kasulik näidata valitud
andmevahemikku ka jooniste juures. Selleks sobib väike ühe reaga tabel.

Tee sammud Superseti veebiliideses.

1. Ava **Charts**.
2. Vajuta **+ Chart**.
3. Vali dataset:

```text
v_dashboard_kpi
```

4. Vali visualiseerimistüüp:

```text
Table
```

5. Vajuta **Create new chart**.
6. Vali päringu režiimiks **Aggregate**.
7. Jäta **Group by** tühjaks.
8. Lisa kaks mõõdikut:

| Mõõdik | Nimi |
|--------|------|
| `MIN(sales_date)` | `Perioodi algus` |
| `MAX(sales_date)` | `Perioodi lõpp` |

Kui Superset kuvab veerud eesti keeles, vali mõõdiku aluseks `Müügikuupäev`.
Koondamisviisid on vastavalt `MIN` ja `MAX`.

9. Sea `Time range` väärtuseks `No filter`.
10. Vajuta **Run**.
11. Salvesta joonis nimega:

```text
Valitud müügiperiood
```

12. Lisa see dashboardile ja rakenda talle sama `Müügikuupäev` ajafilter.

Oodatav tulemus:

Tabel näitab valitud filtrivahemikus tegelikult olemas olevate müügiandmete
algus- ja lõppkuupäeva. Kui valitud vahemikus mõnel päeval andmeid ei ole,
võib kuvatud algus või lõpp erineda filtri tehnilisest piirist. See on hea
meeldetuletus: dashboard näitab olemasolevaid andmeid, mitte ainult filtri
seadistust.

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
