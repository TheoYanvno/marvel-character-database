"""Database layer: builds the SQLite database and runs every query.

The app's queries live in sql/app_queries.sql (shared with the live demo) and use parameterized queries (?) to prevent SQL injection.
"""
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "sql" / "schema.sql"
DATA = ROOT / "data" / "characters.json"
QUERIES_FILE = ROOT / "sql" / "app_queries.sql"


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


def load_queries(path=QUERIES_FILE):
    """Read the named queries ("-- name: x") from sql/app_queries.sql into a dict."""
    queries, name = {}, None
    for line in Path(path).read_text().splitlines():
        match = re.match(r"--\s*name:\s*(\w+)", line)
        if match:
            name = match.group(1)
            queries[name] = ""
        elif name and not line.lstrip().startswith("--"):
            queries[name] += line + "\n"
    return {k: v.strip() for k, v in queries.items()}


Q = load_queries()


def _rows(conn, name, *params):
    return [dict(r) for r in conn.execute(Q[name], params)]


def search(conn, text=""):
    """Card list. Matches hero name, real name or a power."""
    like = f"%{text.strip()}%"
    return _rows(conn, "search", like, like, like)


def get_character(conn, character_id):
    """Full profile: one query per related table."""
    c = conn.execute(Q["character"], (character_id,)).fetchone()
    if c is None:
        return None
    profile = dict(c)
    profile["powers"] = [r["name"] for r in _rows(conn, "character_powers", character_id)]
    profile["teams"] = [r["name"] for r in _rows(conn, "character_teams", character_id)]
    profile["relationships"] = _rows(conn, "character_relationships", character_id)
    profile["appearances"] = _rows(conn, "character_appearances", character_id)
    return profile


def stats(conn):
    """Aggregate queries for the stats bar."""
    return {
        "by_alignment": _rows(conn, "stats_by_alignment"),
        "top_powers": _rows(conn, "stats_top_powers"),
        "by_decade": _rows(conn, "stats_by_decade"),
    }
