"""
REST API andmete serveerimiseks (02_api.py)

Serveerib marts-skeemi koondtabeleid JSON-vormingus.
Autentimine: X-API-Key päis (väärtus .env-st API_KEY).

Käivitamine:
  docker compose exec python uvicorn 02_api:app --host 0.0.0.0 --port 8000 --reload

Testimine:
  curl -H "X-API-Key: <API_KEY>" http://localhost:8000/api/myyk/kuus
  curl http://localhost:8000/docs   (interaktiivne dokumentatsioon)
"""

import os
from typing import Any

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

app = FastAPI(
    title="Praktikum 9 — Andmete serveerimine",
    description="Supermarketi müügiandmete REST API. Autentimine: X-API-Key päis.",
    version="1.0.0",
)

# --- Autentimine ---

API_KEY = os.environ.get("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_header)) -> str:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY on serveris seadistamata")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Vigane või puuduv API-võti")
    return key


# --- Andmebaasiühendus ---

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "praktikum"),
        password=os.environ.get("DB_PASSWORD", "praktikum"),
        dbname=os.environ.get("DB_NAME", "praktikum"),
    )


def query(sql: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


# --- Lõpp-punktid ---

@app.get(
    "/api/myyk/kuus",
    summary="Igakuine müük",
    description="Tagastab mart_myyk_kuus koondtabeli: tulu, tehingute arv ja keskmine ostu suurus kuu lõikes.",
)
def myyk_kuus(_: str = Security(require_api_key)):
    return query("SELECT * FROM marts.mart_myyk_kuus ORDER BY month_start")


@app.get(
    "/api/myyk/kategooria",
    summary="Müük tootekategooria järgi",
    description="Tagastab mart_myyk_kategooria: müük kategooria ja kuu lõikes.",
)
def myyk_kategooria(_: str = Security(require_api_key)):
    return query("SELECT * FROM marts.mart_myyk_kategooria ORDER BY month_start, category")


@app.get(
    "/api/myyk/piirkond",
    summary="Müük piirkonna järgi",
    description="Tagastab mart_myyk_piirkond: müük piirkonna ja kuu lõikes.",
)
def myyk_piirkond(_: str = Security(require_api_key)):
    return query("SELECT * FROM marts.mart_myyk_piirkond ORDER BY month_start, region")
