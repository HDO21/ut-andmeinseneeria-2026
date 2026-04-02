CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS staging.user_status (
    email TEXT PRIMARY KEY,
    account_status TEXT NOT NULL,
    source_system TEXT NOT NULL,
    updated_at DATE
);

CREATE TABLE IF NOT EXISTS staging.api_users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT,
    company_name TEXT,
    loaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.user_profile (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT,
    company_name TEXT,
    account_status TEXT,
    source_system TEXT,
    loaded_at TIMESTAMP DEFAULT NOW()
);
