# Marvel Character Database

**▶ [Live demo](https://theoyanvno.github.io/marvel-character-database/)**

A Python + SQL web app for exploring 133 Marvel characters (63 heroes, 52 villains and 18 antiheroes), grouped into **Heroes**, **Villains** and **Antiheroes**. Type a name, real name or power (try "flight"), switch between sections, or click a card. The selected card slides to the side and the character's profile appears next to it: origin, powers, teams, relationships, and a timeline of pop culture highlights.

**Tech:** Python · Flask · SQLite (`sqlite3`) · SQL · vanilla JavaScript · CSS animations · `unittest`

| Card grid | Character profile |
|---|---|
| ![Cards](docs/cards.png) | ![Profile](docs/profile.png) |

## Database design

Seven related tables ([`sql/schema.sql`](sql/schema.sql)):

```
characters ──< character_powers >── powers
     │    └──< character_teams  >── teams
     ├──< relationships  (related_id links back to characters when that person is in the database)
     └──< appearances    (comic, film, TV, animation; year and notes)
```

- **Many-to-many** relationships through link tables (`character_powers`, `character_teams`) with composite primary keys
- **Foreign keys**, `CHECK` constraints (alignment, relationship kind, medium), `UNIQUE` names and indexes
- Data loads from [`data/characters.json`](data/characters.json) in a single transaction, then an `UPDATE` with a subquery links relationships to characters that exist in the database

## SQL highlights

The app's queries live in [`sql/app_queries.sql`](sql/app_queries.sql), loaded by [`app/db.py`](app/db.py), and use parameterized statements (`?`) to prevent SQL injection. More to explore in [`sql/queries.sql`](sql/queries.sql):

- Search across three tables with `LEFT JOIN` + `LIKE`
- Powers shared by several characters with `GROUP BY`, `HAVING` and `GROUP_CONCAT`
- Characters on no team with `LEFT JOIN … IS NULL`
- Rivalries where both characters are in the database (joining `characters` twice)
- Years between a character's comic debut and first film with a correlated subquery
- Search plus an optional side filter in one query: `(name LIKE ? OR …) AND (? = '' OR alignment = ?)`, where an empty side means everyone
- Debuts per decade with integer math in `GROUP BY`

## API

| Method | Endpoint | Returns |
|---|---|---|
| GET | `/api/characters?q=text` | Matching cards (name, real name or power) |
| GET | `/api/characters/<id>` | Full profile, or 404 |
| GET | `/api/characters?side=villain` | Only heroes, villains or antiheroes (combine with `q`) |
| GET | `/api/sides` | How many characters are on each side |
| GET | `/api/stats` | Counts by alignment, most common powers, debuts per decade |

## Live demo: the same SQL in the browser

GitHub Pages can only host static files, so it can't run the Flask server. The live demo still runs real SQL:

1. [`build_site.py`](build_site.py) builds the SQLite database file with the same Python code the app uses and writes the site to `docs/`.
2. In the browser, [`static-api.js`](app/static/static-api.js) downloads that database and runs it with [sql.js](https://sql.js.org) (SQLite compiled to WebAssembly).
3. Both the Flask app and the browser load their queries from the same file, [`sql/app_queries.sql`](sql/app_queries.sql), so the live demo runs exactly the same SQL as the server.

The front end calls one small data layer (`api.cards()`, `api.sides()`, `api.character()`), so it doesn't need to know which version it's talking to.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main                                  # http://localhost:5000
python -m unittest discover -s tests -t .           # 15 tests
python build_db.py                                  # optional: writes marvel.db to explore in DB Browser for SQLite
python build_site.py                                # rebuilds the live demo in docs/
```

## Add a character

Add an entry to `data/characters.json` (same fields as the others) and restart the app. The database is rebuilt from the JSON file on startup. Run `python build_site.py` to update the live demo.

## Notes

- Unofficial fan project for learning Python and SQL. Not affiliated with or endorsed by Marvel. Character summaries are written in my own words, and the cards use initials instead of artwork.
- Built with help from AI coding tools for planning, code review and tests.
