CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capital TEXT NOT NULL,
    population BIGINT,
    area_km2 BIGINT,
    continent TEXT NOT NULL
);
