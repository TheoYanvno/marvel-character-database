import json
import sqlite3
import unittest
from pathlib import Path

from app import db

COUNT = len(json.loads((Path(__file__).parent.parent / 'data' / 'characters.json').read_text()))


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.build(db.connect())

    def test_loads_all_characters(self):
        count = self.conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
        self.assertEqual(count, COUNT)

    def test_search_by_power(self):
        names = [c["hero_name"] for c in db.search(self.conn, "flight")]
        self.assertIn("Storm", names)
        self.assertIn("Iron Man", names)
        self.assertNotIn("Black Widow", names)

    def test_profile_includes_related_tables(self):
        spidey = db.search(self.conn, "Peter Parker")[0]
        profile = db.get_character(self.conn, spidey["id"])
        self.assertIn("Spider-sense", profile["powers"])
        self.assertEqual(profile["appearances"][0]["year"], 1962)
        mentor = next(r for r in profile["relationships"] if r["kind"] == "mentor")
        self.assertIsNotNone(mentor["id"])   # Iron Man is linked to his own record

    def test_heroes_and_villains_sections(self):
        heroes = db.search(self.conn, side="hero")
        villains = db.search(self.conn, side="villain")
        self.assertTrue(heroes and villains)
        self.assertTrue(all(c["alignment"] == "hero" for c in heroes))
        self.assertIn("Green Goblin", [c["hero_name"] for c in villains])
        self.assertEqual(db.search(self.conn, "goblin", side="hero"), [])        # search and side combine
        self.assertEqual(len(db.search(self.conn, side="nonsense")), COUNT)     # unknown side = everyone
        self.assertEqual(sum(db.side_counts(self.conn).values()), COUNT)

    def test_new_enemy_links_to_existing_record(self):
        spidey = db.search(self.conn, "Peter Parker")[0]
        goblin = next(r for r in db.get_character(self.conn, spidey["id"])["relationships"] if r["name"] == "Green Goblin")
        self.assertIsNotNone(goblin["id"])           # Spider-Man's enemy now has its own profile

    def test_missing_character_returns_none(self):
        self.assertIsNone(db.get_character(self.conn, 999))

    def test_constraints_reject_bad_data(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO relationships (character_id, related_name, kind) VALUES (1, 'X', 'frenemy')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO character_powers VALUES (999, 1)")

    def test_stats(self):
        s = db.stats(self.conn)
        self.assertEqual(sum(r["total"] for r in s["by_alignment"]), COUNT)
        self.assertTrue(all(r["characters"] > 1 for r in s["top_powers"]))


if __name__ == "__main__":
    unittest.main()
