-- Queries used by the app. Each one starts with a "-- name:" line.
-- The Flask app (app/db.py) and the live demo in the browser (app/static/static-api.js)
-- both load this file, so the exact same SQL runs in both places.
-- Parameters use ? placeholders, so user input is never pasted into the SQL (prevents SQL injection).

-- name: search
-- Card list. Matches hero name, real name or a power, optionally only one side
-- (hero, villain or antihero; an empty string means all). Characters whose hero name starts with the
-- search come first, then other name matches, then power matches.
-- Params: like, like, like, side, side, prefix, like, like
SELECT c.id, c.hero_name, c.real_name, c.alignment, c.first_year, c.color
FROM characters c
WHERE EXISTS (
        SELECT 1 FROM character_powers cp JOIN powers p ON p.id = cp.power_id
        WHERE cp.character_id = c.id AND p.name LIKE ?
      ) OR c.hero_name LIKE ? OR c.real_name LIKE ?
GROUP BY c.id
HAVING (? = '' OR c.alignment = ?)
ORDER BY CASE WHEN c.hero_name LIKE ? THEN 0
              WHEN c.hero_name LIKE ? OR c.real_name LIKE ? THEN 1
              ELSE 2 END,
         c.hero_name;

-- name: side_counts
-- How many characters are on each side, for the section tabs
SELECT alignment, COUNT(*) AS total FROM characters GROUP BY alignment;

-- name: character
SELECT * FROM characters WHERE id = ?;

-- name: character_powers
SELECT p.name FROM powers p
JOIN character_powers cp ON cp.power_id = p.id
WHERE cp.character_id = ? ORDER BY p.name;

-- name: character_teams
SELECT t.name FROM teams t
JOIN character_teams ct ON ct.team_id = t.id
WHERE ct.character_id = ? ORDER BY t.name;

-- name: character_relationships
SELECT related_name AS name, related_id AS id, kind
FROM relationships WHERE character_id = ?
ORDER BY CASE kind WHEN 'family' THEN 1 WHEN 'romance' THEN 2 WHEN 'mentor' THEN 3
                   WHEN 'ally' THEN 4 ELSE 5 END, related_name;

-- name: character_appearances
SELECT medium, title, year, note FROM appearances
WHERE character_id = ? ORDER BY year;

-- name: stats_by_alignment
SELECT alignment, COUNT(*) AS total FROM characters GROUP BY alignment ORDER BY total DESC;

-- name: stats_top_powers
SELECT p.name, COUNT(*) AS characters
FROM powers p JOIN character_powers cp ON cp.power_id = p.id
GROUP BY p.id HAVING COUNT(*) > 1
ORDER BY characters DESC, p.name LIMIT 5;

-- name: stats_by_decade
SELECT (first_year / 10) * 10 AS decade, COUNT(*) AS debuts
FROM characters GROUP BY decade ORDER BY decade;
