import os

SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URI"]
SECRET_KEY = os.environ["SECRET_KEY"]

# Õppekeskkonnas hoiame vahemälu lihtsa ja lühikese.
# Nii on näha, kuidas cron lisab andmeid ja dashboard värskendab päringuid.
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 5,
}
DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 5,
}
FILTER_STATE_CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache"}
EXPLORE_FORM_DATA_CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache"}

DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [0, "Ära värskenda"],
    [30, "30 sekundit"],
    [60, "1 minut"],
    [300, "5 minutit"],
]

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

WTF_CSRF_ENABLED = True
