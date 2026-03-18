TRUNCATE TABLE countries;

COPY countries (id, name, capital, population, area_km2, continent)
FROM '/data/countries.csv'
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ',',
    ENCODING 'UTF8'
);
