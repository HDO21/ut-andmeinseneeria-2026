# Edenemisraport

See fail on näidis projektitöö teise nädala väljundiks. Enda projektis uuenda seda lühidalt iga esitamise eel.

## Mis on valmis

- Docker Compose käivitab PostgreSQL-i, töövoo konteineri ja näidikulaua.
- Open-Meteo API-st saab kätte Tartu ja Tallinna tunnipõhise prognoosi.
- Andmed liiguvad `staging` kihist `mart` kihti.
- Näidikulaud näitab temperatuuri, sademeid, tuult ja kvaliteediteste.

## Järgmised sammud

- Kontrollida, kas valitud mõõdikud vastavad äriküsimusele piisavalt hästi.
- Lisada vajadusel kolmas asukoht või teine ilmamuutuja.
- Täpsustada README järelduste ja piirangute osa.

## Mis takistab

- Kui Open-Meteo API pole ajutiselt kättesaadav, tuleb laadimine hiljem uuesti käivitada.
- Kui port `8501` on hõivatud, tuleb `.env` failis muuta `DASHBOARD_PORT_HOST` väärtust.

## Kontrollpunkt

Viimane edukas käsurea kontroll:

```bash
docker compose exec pipeline python scripts/run_pipeline.py check
```

Oodatav tulemus: viimase laadimise real on `status = success` ja kvaliteeditestide olek on `passed`.
