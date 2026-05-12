#!/bin/sh
set -eu

# Cron kirjutab oma töövoo logi faili. Sama fail on `logs/` kausta kaudu
# nähtav ka hostis, seega saab õppija seda vajadusel lugeda ilma konteinerisse
# sisse minemata.
mkdir -p /var/log/praktikum
touch /var/log/praktikum/pipeline.log

# Konteineri kell seatakse Tallinna ajavööndisse, et logide ajad oleksid samad,
# mida õppija Supersetis näeb.
ln -snf "/usr/share/zoneinfo/${TZ:-Europe/Tallinn}" /etc/localtime
echo "${TZ:-Europe/Tallinn}" > /etc/timezone

# Paigaldame praktikumi crontab'i. See fail ütleb, et mikrobatch käivitub iga
# minuti järel. `sed` eemaldab vajadusel Windowsi CRLF reavahetuse märgi.
sed 's/\r$//' /app/scheduler/crontab > /tmp/praktikum-crontab
crontab /tmp/praktikum-crontab

echo "[scheduler] Cron käivitus $(date --iso-8601=seconds)" >> /var/log/praktikum/pipeline.log

# Käivitame ühe mikrobatch'i kohe, et dashboard hakkaks pärast avamist muutuma
# ka siis, kui järgmise cron-minutini on veel veidi aega.
cd /app
/usr/local/bin/python scripts/microbatch.py run-scheduled >> /var/log/praktikum/pipeline.log 2>&1

# `cron -f` hoiab konteineri töös. Ilma selleta lõpeks konteiner kohe pärast
# esimest käivitust ära.
exec cron -f
