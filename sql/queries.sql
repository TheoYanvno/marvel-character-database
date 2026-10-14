-- Example queries to explore the database (run with: sqlite3 marvel.db < sql/queries.sql)

-- 1) Every character and their team(s): many-to-many JOIN through a link table
SELECT c.hero_name, t.name AS team
FROM characters c
JOIN character_teams ct ON ct.character_id = c.id
JOIN teams t            ON t.id = ct.team_id
ORDER BY t.name, c.hero_name;

-- 2) Powers shared by more than one character: GROUP BY + HAVING
SELECT p.name, COUNT(*) AS characters, GROUP_CONCAT(c.hero_name, ', ') AS who
FROM powers p
JOIN character_powers cp ON cp.power_id = p.id
JOIN characters c        ON c.id = cp.character_id
GROUP BY p.id
HAVING COUNT(*) > 1
ORDER BY characters DESC;

-- 3) Characters who are on no team: LEFT JOIN + IS NULL
SELECT c.hero_name
FROM characters c
LEFT JOIN character_teams ct ON ct.character_id = c.id
WHERE ct.character_id IS NULL;

-- 4) Rivalries inside the database: join relationships to characters twice (both sides)
SELECT a.hero_name AS character, b.hero_name AS enemy
FROM relationships r
JOIN characters a ON a.id = r.character_id
JOIN characters b ON b.id = r.related_id
WHERE r.kind = 'enemy';

-- 5) Years between comic debut and first film: correlated subquery
SELECT c.hero_name, c.first_year,
       (SELECT MIN(year) FROM appearances a WHERE a.character_id = c.id AND a.medium = 'film') AS first_film,
       (SELECT MIN(year) FROM appearances a WHERE a.character_id = c.id AND a.medium = 'film') - c.first_year AS years_waited
FROM characters c
ORDER BY years_waited DESC;

-- 6) Debuts per decade
SELECT (first_year / 10) * 10 AS decade, COUNT(*) AS debuts
FROM characters
GROUP BY decade
ORDER BY decade;
