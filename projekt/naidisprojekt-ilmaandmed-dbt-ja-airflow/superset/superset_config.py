import os

# Superset metaandmebaasi ühendus
SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://"
    f"{os.environ.get('SUPERSET_DB_USER', 'superset')}:"
    f"{os.environ.get('SUPERSET_DB_PASSWORD', 'superset')}@"
    f"{os.environ.get('SUPERSET_DB_HOST', 'superset-db')}:5432/"
    f"{os.environ.get('SUPERSET_DB_NAME', 'superset')}"
)

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "supersetsecretkey123")

# Arenguks sobiv seadistus (produktsioonikeskkonnas lülita sisse)
TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = False
