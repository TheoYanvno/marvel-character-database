-- Queries used by the app. Each one starts with a "-- name:" line.
-- The Flask app (app/db.py) and the live demo in the browser (app/static/static-api.js)
-- both load this file, so the exact same SQL runs in both places.
-- Parameters use ? placeholders, so user input is never pasted into the SQL (prevents SQL injection).

-- name: search
-- Card list. Matches hero name, real name, a power or the MCU actor, optionally only one side
-- (hero, villain or antihero; an empty string means all). Characters whose hero name starts with the
-- search come first, then other name matches, then power and actor matches.
-- Params: like, like, like, like, side, side, prefix, like, like
SELECT c.id, c.hero_name, c.real_name, c.alignment, c.first_year, c.color
FROM characters c
WHERE EXISTS (
        SELECT 1 FROM character_powers cp JOIN powers p ON p.id = cp.power_id
        WHERE cp.character_id = c.id AND p.name LIKE ?
      ) OR c.hero_name LIKE ? OR c.real_name LIKE ? OR c.mcu_actor LIKE ?
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
-- Everyone connected to a character: the pairs stored on their own record, plus pairs stored on the
-- other person's record (UNION), so a relationship only has to be entered once.
-- A mentor seen from the other side is a protégé.
-- Params: id, id, id
-- alignment, color and real_name come along for linked people so enemies can be drawn as mini cards.
SELECT name, id, kind, detail, alignment, color, real_name FROM (
  SELECT r.related_name AS name, r.related_id AS id, r.kind, r.detail, rc.alignment, rc.color, rc.real_name
  FROM relationships r LEFT JOIN characters rc ON rc.id = r.related_id
  WHERE r.character_id = ?
  UNION
  SELECT c.hero_name, c.id, r.kind,
         CASE r.detail WHEN 'mentor' THEN 'protégé' WHEN 'protégé' THEN 'mentor' ELSE r.detail END,
         c.alignment, c.color, c.real_name
  FROM relationships r JOIN characters c ON c.id = r.character_id
  WHERE r.related_id = ?
    AND NOT EXISTS (SELECT 1 FROM relationships mine
                    WHERE mine.character_id = ? AND mine.related_id = c.id AND mine.kind = r.kind)
)
ORDER BY CASE kind WHEN 'family' THEN 1 WHEN 'romantic' THEN 2 WHEN 'friend' THEN 3 ELSE 4 END,
         CASE alignment WHEN 'villain' THEN 1 WHEN 'antihero' THEN 2 WHEN 'hero' THEN 3 ELSE 4 END, name;

-- name: character_appearances
SELECT medium, title, year, note FROM appearances
WHERE character_id = ? ORDER BY year;

-- name: character_mcu_titles
-- Movies and series in release order; the first row is their first MCU appearance
SELECT t.title, t.kind, COALESCE(r.year, t.year) AS year
FROM mcu_roles r JOIN mcu_titles t ON t.id = r.title_id
WHERE r.character_id = ?
ORDER BY COALESCE(r.year, t.year), t.id;

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

-- name: stats_most_mcu_titles
SELECT c.hero_name, COUNT(*) AS titles
FROM characters c JOIN mcu_roles r ON r.character_id = c.id
GROUP BY c.id ORDER BY titles DESC, c.hero_name LIMIT 5;

-- name: stats_biggest_rogues_galleries
-- Heroes with the most enemies, counting pairs stored on either side
SELECT c.hero_name, COUNT(DISTINCT CASE WHEN r.character_id = c.id THEN 'n:' || r.related_name
                                          ELSE 'id:' || r.character_id END) AS enemies
FROM characters c
JOIN relationships r ON r.kind = 'enemy' AND (r.character_id = c.id OR r.related_id = c.id)
WHERE c.alignment = 'hero'
GROUP BY c.id ORDER BY enemies DESC, c.hero_name LIMIT 5;
