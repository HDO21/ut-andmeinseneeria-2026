# Praktikum 3: Andmete integreerimine (Edasijõudnud)

## Eesmärk

Ehitada inkrementaalne, logitud ja veahaldusega andmete laadimise protsess. Praktikumi lõpuks oskad kirjeldada idempotentsust ja rakendada seda praktikas.

## Õpiväljundid

Praktikumi lõpuks osaleja:

- Suudab teha inkrementaalse andmete laadimise (ainult uued/muutunud andmed)
- Oskab kirjeldada idempotentsust ja rakendada seda ETL protsessis
- Ehitab ETL-i nii, et see on logitud ja vead on hallatavad
- Tunneb dbt transformatsioonitööriista põhimõtteid

## Teemad

| Teema | Kirjeldus |
|-------|-----------|
| Inkrementaalne laadimine | Ainult uute/muutunud andmete laadimine |
| Idempotentsus | ETL protsessi korratavus ilma kõrvalmõjudeta |
| Veahaldus | Vigade püüdmine, logimine ja taastamine |
| dbt | Transformatsioonikiht SQL-põhiste mudelitega |

## Eeldused

- Docker ja Docker Compose on paigaldatud
- Kogemus PostgreSQL, SQL ja Python-iga
- Töötav ETL protsess eelmistest praktikumidest
- Arusaam ETL etappidest (baastase teadmised)

## Uued mõisted

| Mõiste | Selgitus |
|--------|----------|
| **Inkrementaalne laadimine** | Laetakse ainult andmed, mis on lisandunud või muutunud pärast viimast laadimist |
| **Idempotentsus** | Sama operatsiooni korduv käivitamine annab alati sama tulemuse |
| **dbt** | Data Build Tool — SQL-põhine transformatsioonitööriist, mis muudab andmebaasis olevaid andmeid |
| **Staging layer** | Vahekiht, kuhu toorandmed esmalt laetakse enne transformeerimist |
| **Watermark** | Ajatempel või järjekorranumber, mis näitab, kust viimane laadimine pooleli jäi |
