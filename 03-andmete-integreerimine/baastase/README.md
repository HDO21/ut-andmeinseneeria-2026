# Praktikum 3: Andmete integreerimine (Baastase)

## Eesmärk

Õppida andmeid koguma erinevatest allikatest (CSV, Parquet, API), puhastama neid ja laadima andmebaasi. Praktikumi lõpuks oskad selgitada ETL etappe oma sõnadega.

## Õpiväljundid

Praktikumi lõpuks osaleja:

- Suudab võtta ühe allika (CSV, Parquet või API) ja laadida andmed andmebaasi
- Oskab andmeid puhastada ja ette valmistada enne laadimist
- Mõistab ETL (Extract, Transform, Load) etappe ja oskab neid selgitada
- Tunneb erinevaid andmeformaate ja nende eripärasid

## Teemad

| Teema | Kirjeldus |
|-------|-----------|
| Andmeallikad | CSV, Parquet, JSON ja REST API-d |
| Extract | Andmete lugemine erinevatest allikatest |
| Transform | Andmete puhastamine, tüübiteisendused, duplikaatide eemaldamine |
| Load | Andmete laadimine PostgreSQL andmebaasi |

## Eeldused

- Docker ja Docker Compose on paigaldatud
- Eelmiste praktikumide kogemus PostgreSQL-iga
- Põhiteadmised SQL-ist ja Python-ist

## Uued mõisted

| Mõiste | Selgitus |
|--------|----------|
| **ETL** | Extract-Transform-Load — andmete kogumise, teisendamise ja laadimise protsess |
| **Parquet** | Veerupõhine andmeformaat, mis on optimeeritud analüütika jaoks |
| **Idempotentsus** | Sama operatsiooni korduv käivitamine annab alati sama tulemuse |
| **Andmete puhastamine** | Vigaste, puuduvate või ebakonsistentsete andmete parandamine |
