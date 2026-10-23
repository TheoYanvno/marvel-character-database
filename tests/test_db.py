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
        mentor = next(r for r in profile["relationships"] if r["detail"] == "mentor")
        self.assertEqual((mentor["name"], mentor["kind"]), ("Iron Man", "friend"))
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

    def test_mcu_appearances(self):
        spidey = db.get_character(self.conn, db.search(self.conn, "Peter Parker")[0]["id"])
        self.assertEqual(spidey["mcu_actor"], "Tom Holland")
        self.assertIn("Doctor Strange", spidey["mcu_lore"])
        self.assertEqual(spidey["mcu_titles"][0], {"title": "Captain America: Civil War", "kind": "film", "year": 2016})
        years = [t["year"] for t in spidey["mcu_titles"]]
        self.assertEqual(years, sorted(years))                       # release order
        punisher = db.get_character(self.conn, db.search(self.conn, "Frank Castle")[0]["id"])
        self.assertEqual(punisher["mcu_titles"][0], {"title": "Daredevil", "kind": "series", "year": 2016})  # season 2
        storm = db.get_character(self.conn, db.search(self.conn, "Ororo")[0]["id"])
        self.assertEqual(storm["mcu_titles"], [])
        self.assertIn("Not in the MCU yet", storm["mcu_note"])
        missing = self.conn.execute("""SELECT hero_name FROM characters
            WHERE (mcu_lore IS NULL) = (mcu_note IS NULL)""").fetchall()
        self.assertEqual(missing, [])                 # everyone has either an MCU story or a note

    def test_search_by_actor(self):
        self.assertEqual([c["hero_name"] for c in db.search(self.conn, "Hiddleston")], ["Loki"])
        self.assertEqual(db.search(self.conn, "Thor")[0]["hero_name"], "Thor")   # names still rank first

    def test_unknown_mcu_title_is_rejected(self):
        bad = Path(self.id().replace(".", "_") + ".json")
        bad.write_text(json.dumps([{**json.loads(Path(db.DATA).read_text())[0],
                                    "mcu": {"actor": "X", "titles": ["Not A Real Movie"]}}]))
        try:
            with self.assertRaises(ValueError):
                db.build(db.connect(), data_file=bad)
        finally:
            bad.unlink()

    def test_relationships_show_on_both_pages(self):
        def rels(name):
            return db.get_character(self.conn, db.search(self.conn, name)[0]["id"])["relationships"]
        iron_man = rels("Tony Stark")
        spidey = next(r for r in iron_man if r["name"] == "Spider-Man")      # stored on Spider-Man's record
        self.assertEqual((spidey["kind"], spidey["detail"]), ("friend", "protégé"))
        self.assertIn("War Machine", [r["name"] for r in iron_man if r["id"]])  # linked by real name James Rhodes
        kinds = {r["kind"] for name in ("Thor", "Loki", "Hela") for r in rels(name)}
        self.assertEqual(kinds, {"family", "friend", "romantic", "enemy"})
        names = [r["name"] for r in rels("Wakanda")] if db.search(self.conn, "Wakanda") else []
        self.assertEqual(names, [])
        for r in rels("Scarlet Witch"):                                     # no one listed twice
            self.assertEqual(sum(1 for x in rels("Scarlet Witch") if (x["name"], x["kind"]) == (r["name"], r["kind"])), 1)

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
        self.assertEqual(s["most_mcu_titles"][0]["hero_name"], "Nick Fury")


if __name__ == "__main__":
    unittest.main()
