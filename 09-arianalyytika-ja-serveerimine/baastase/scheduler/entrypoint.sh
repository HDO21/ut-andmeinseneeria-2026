#!/bin/sh
set -eu

mkdir -p /var/log/praktikum
touch /var/log/praktikum/pipeline.log

ln -snf "/usr/share/zoneinfo/${TZ:-Europe/Tallinn}" /etc/localtime
echo "${TZ:-Europe/Tallinn}" > /etc/timezone

crontab /app/scheduler/crontab

echo "[scheduler] Cron käivitus $(date --iso-8601=seconds)" >> /var/log/praktikum/pipeline.log

# Käivitame ühe mikrobatch'i kohe, et dashboard hakkaks pärast avamist muutuma
# ka siis, kui järgmise cron-minutini on veel veidi aega.
cd /app
/usr/local/bin/python scripts/microbatch.py run-scheduled >> /var/log/praktikum/pipeline.log 2>&1

exec cron -f
