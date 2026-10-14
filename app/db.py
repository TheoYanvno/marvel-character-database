"""Database layer: builds the SQLite database and runs every query.

All SQL lives here and uses parameterized queries (?) to prevent SQL injection.
"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "sql" / "schema.sql"
DATA = ROOT / "data" / "characters.json"


def connect(path=":memory:"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _get_or_create(conn, table, name):
    row = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    return conn.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,)).lastrowid


def build(conn, data_file=DATA):
    """Create the tables and load characters.json inside one transaction."""
    conn.executescript(SCHEMA.read_text())
    characters = json.loads(Path(data_file).read_text())
    with conn:
        for c in characters:
            cid = conn.execute(
                """INSERT INTO characters
                   (hero_name, real_name, alignment, first_appearance, first_year, creators, origin, color)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (c["hero_name"], c["real_name"], c["alignment"], c["first_appearance"],
                 c["first_year"], c["creators"], c["origin"], c["color"]),
            ).lastrowid
            for power in c["powers"]:
                conn.execute("INSERT INTO character_powers VALUES (?, ?)",
                             (cid, _get_or_create(conn, "powers", power)))
            for team in c["teams"]:
                conn.execute("INSERT INTO character_teams VALUES (?, ?)",
                             (cid, _get_or_create(conn, "teams", team)))
            for name, kind in c["relationships"]:
                conn.execute("INSERT INTO relationships (character_id, related_name, kind) VALUES (?, ?, ?)",
                             (cid, name, kind))
            for medium, title, year, note in c["appearances"]:
                conn.execute("INSERT INTO appearances (character_id, medium, title, year, note) VALUES (?, ?, ?, ?, ?)",
                             (cid, medium, title, year, note))
        # Link relationships to characters that exist in the database (UPDATE with a subquery)
        conn.execute("""
            UPDATE relationships
            SET related_id = (SELECT id FROM characters WHERE hero_name = relationships.related_name)
            WHERE related_name IN (SELECT hero_name FROM characters)""")
    return conn


def search(conn, text=""):
    """Card list. Matches hero name, real name or a power."""
    like = f"%{text.strip()}%"
    rows = conn.execute("""
        SELECT DISTINCT c.id, c.hero_name, c.real_name, c.alignment, c.first_year, c.color
        FROM characters c
        LEFT JOIN character_powers cp ON cp.character_id = c.id
        LEFT JOIN powers p            ON p.id = cp.power_id
        WHERE c.hero_name LIKE ? OR c.real_name LIKE ? OR p.name LIKE ?
        ORDER BY c.hero_name""", (like, like, like)).fetchall()
    return [dict(r) for r in rows]


def get_character(conn, character_id):
    """Full profile: one query per related table."""
    c = conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
    if c is None:
        return None
    profile = dict(c)
    profile["powers"] = [r["name"] for r in conn.execute("""
        SELECT p.name FROM powers p
        JOIN character_powers cp ON cp.power_id = p.id
        WHERE cp.character_id = ? ORDER BY p.name""", (character_id,))]
    profile["teams"] = [r["name"] for r in conn.execute("""
        SELECT t.name FROM teams t
        JOIN character_teams ct ON ct.team_id = t.id
        WHERE ct.character_id = ? ORDER BY t.name""", (character_id,))]
    profile["relationships"] = [dict(r) for r in conn.execute("""
        SELECT related_name AS name, related_id AS id, kind
        FROM relationships WHERE character_id = ?
        ORDER BY CASE kind WHEN 'family' THEN 1 WHEN 'romance' THEN 2 WHEN 'mentor' THEN 3
                           WHEN 'ally' THEN 4 ELSE 5 END, related_name""", (character_id,))]
    profile["appearances"] = [dict(r) for r in conn.execute("""
        SELECT medium, title, year, note FROM appearances
        WHERE character_id = ? ORDER BY year""", (character_id,))]
    return profile


def stats(conn):
    """Aggregate queries for the stats bar."""
    return {
        "by_alignment": [dict(r) for r in conn.execute("""
            SELECT alignment, COUNT(*) AS total FROM characters GROUP BY alignment ORDER BY total DESC""")],
        "top_powers": [dict(r) for r in conn.execute("""
            SELECT p.name, COUNT(*) AS characters
            FROM powers p JOIN character_powers cp ON cp.power_id = p.id
            GROUP BY p.id HAVING COUNT(*) > 1
            ORDER BY characters DESC, p.name LIMIT 5""")],
        "by_decade": [dict(r) for r in conn.execute("""
            SELECT (first_year / 10) * 10 AS decade, COUNT(*) AS debuts
            FROM characters GROUP BY decade ORDER BY decade""")],
    }
