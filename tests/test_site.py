import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import build_site
from app import db


class SharedQueryTests(unittest.TestCase):
    def test_all_named_queries_load_and_are_valid_sql(self):
        conn = db.build(db.connect())
        expected = {"search", "character", "character_powers", "character_teams",
                    "character_relationships", "character_appearances",
                    "stats_by_alignment", "stats_top_powers", "stats_by_decade"}
        self.assertEqual(set(db.Q), expected)
        for name, sql in db.Q.items():
            params = (None,) * sql.count("?")
            conn.execute("EXPLAIN " + sql, params)   # raises if the SQL is invalid


class LiveDemoBuildTests(unittest.TestCase):
    def test_build_writes_a_working_static_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_site.build(tmp)
            out = Path(tmp)
            for name in ("index.html", "app.js", "static-api.js", "style.css", "app_queries.sql", "marvel.db"):
                self.assertTrue((out / name).exists(), name)
            html = (out / "index.html").read_text()
            self.assertIn("sql-wasm.js", html)
            self.assertNotIn("/static/", html)         # relative paths only, for GitHub Pages
            conn = sqlite3.connect(out / "marvel.db")
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0], len(json.loads((Path(__file__).parent.parent / "data" / "characters.json").read_text())))
            conn.close()
