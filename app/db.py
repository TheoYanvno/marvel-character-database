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
TITLES = ROOT / "data" / "mcu_titles.json"
IMAGES = ROOT / "app" / "static" / "images"     # card photos; see the README in that folder
IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".webp")
QUERIES_FILE = ROOT / "sql" / "app_queries.sql"


def connect(path=":memory:"):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _image(character, images_dir):
    """The card photo's file name, checked so a typo shows up when the database is built, not as a broken image."""
    name = character.get("image")
    if not name:
        return None
    if "/" in name or "\\" in name or not name.lower().endswith(IMAGE_TYPES):
        raise ValueError(f"{character['hero_name']}: image must be a file name ending in {', '.join(IMAGE_TYPES)}, got {name!r}")
    if not (Path(images_dir) / name).is_file():
        raise ValueError(f"{character['hero_name']}: image {name!r} is not in {images_dir}")
    return name


def _get_or_create(conn, table, name):
    row = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    return conn.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,)).lastrowid


def build(conn, data_file=DATA, titles_file=TITLES, images_dir=IMAGES):
    """Create the tables and load characters.json and mcu_titles.json inside one transaction."""
    conn.executescript(SCHEMA.read_text())
    characters = json.loads(Path(data_file).read_text())
    with conn:
        conn.executemany("INSERT INTO mcu_titles (title, year, kind) VALUES (:title, :year, :kind)",
                         json.loads(Path(titles_file).read_text()))
        for c in characters:
            mcu = c.get("mcu", {})
            cid = conn.execute(
                """INSERT INTO characters
                   (hero_name, real_name, alignment, first_appearance, first_year, creators, origin, color,
                    mcu_actor, mcu_lore, mcu_note, image, image_credit)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (c["hero_name"], c["real_name"], c["alignment"], c["first_appearance"],
                 c["first_year"], c["creators"], c["origin"], c["color"],
                 mcu.get("actor"), mcu.get("lore"), mcu.get("note"),
                 _image(c, images_dir), c.get("image_credit")),
            ).lastrowid
            for t in mcu.get("titles", []):
                # "Title", or ["Title", year] for a later season
                title, year = (t, None) if isinstance(t, str) else t
                row = conn.execute("SELECT id FROM mcu_titles WHERE title = ?", (title,)).fetchone()
                if row is None:
                    raise ValueError(f"{c['hero_name']}: unknown MCU title {title!r}")
                conn.execute("INSERT INTO mcu_roles (character_id, title_id, year) VALUES (?, ?, ?)",
                             (cid, row["id"], year))
            for power in c["powers"]:
                conn.execute("INSERT INTO character_powers VALUES (?, ?)",
                             (cid, _get_or_create(conn, "powers", power)))
            for team in c["teams"]:
                conn.execute("INSERT INTO character_teams VALUES (?, ?)",
                             (cid, _get_or_create(conn, "teams", team)))
            for name, kind, *detail in c["relationships"]:
                conn.execute("INSERT INTO relationships (character_id, related_name, kind, detail) VALUES (?, ?, ?, ?)",
                             (cid, name, kind, detail[0] if detail else None))
            for medium, title, year, note in c["appearances"]:
                conn.execute("INSERT INTO appearances (character_id, medium, title, year, note) VALUES (?, ?, ?, ?, ?)",
                             (cid, medium, title, year, note))
        # Link relationships to characters that exist in the database (UPDATE with a subquery):
        # by hero name, or by real name when exactly one character has it.
        conn.execute("""
            UPDATE relationships
            SET related_id = COALESCE(
                (SELECT id FROM characters WHERE hero_name = relationships.related_name),
                (SELECT CASE WHEN COUNT(*) = 1 THEN MIN(id) END
                 FROM characters WHERE real_name = relationships.related_name))""")
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


SIDES = ("hero", "villain", "antihero")


def search(conn, text="", side=""):
    """Card list. Matches hero name, real name, a power or the MCU actor; side limits it to heroes, villains or antiheroes."""
    like = f"%{text.strip()}%"
    prefix = f"{text.strip()}%"
    side = side if side in SIDES else ""
    return _rows(conn, "search", like, like, like, like, side, side, prefix, like, like)


def side_counts(conn):
    """{'hero': 20, 'villain': 16, 'antihero': 7}"""
    return {r["alignment"]: r["total"] for r in _rows(conn, "side_counts")}


def get_character(conn, character_id):
    """Full profile: one query per related table."""
    c = conn.execute(Q["character"], (character_id,)).fetchone()
    if c is None:
        return None
    profile = dict(c)
    profile["powers"] = [r["name"] for r in _rows(conn, "character_powers", character_id)]
    profile["teams"] = [r["name"] for r in _rows(conn, "character_teams", character_id)]
    profile["relationships"] = _rows(conn, "character_relationships", character_id, character_id, character_id)
    profile["appearances"] = _rows(conn, "character_appearances", character_id)
    profile["mcu_titles"] = _rows(conn, "character_mcu_titles", character_id)
    return profile


def stats(conn):
    """Aggregate queries for the stats bar."""
    return {
        "by_alignment": _rows(conn, "stats_by_alignment"),
        "top_powers": _rows(conn, "stats_top_powers"),
        "by_decade": _rows(conn, "stats_by_decade"),
        "most_mcu_titles": _rows(conn, "stats_most_mcu_titles"),
        "biggest_rogues_galleries": _rows(conn, "stats_biggest_rogues_galleries"),
    }
