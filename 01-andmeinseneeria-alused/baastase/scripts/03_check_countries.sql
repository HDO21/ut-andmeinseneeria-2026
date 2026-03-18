SELECT COUNT(*) AS riikide_arv
FROM countries;

SELECT name, capital, population
FROM countries
ORDER BY population DESC
LIMIT 5;

SELECT continent, COUNT(*) AS riike
FROM countries
GROUP BY continent
ORDER BY riike DESC;
