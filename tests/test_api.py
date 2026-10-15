import json
import unittest
from pathlib import Path

from app.main import app

COUNT = len(json.loads((Path(__file__).parent.parent / 'data' / 'characters.json').read_text()))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list_and_search(self):
        self.assertEqual(len(self.client.get("/api/characters").get_json()), COUNT)
        self.assertEqual(self.client.get("/api/characters?q=wakanda").get_json(), [])

    def test_side_filter_and_counts(self):
        villains = self.client.get("/api/characters?side=villain").get_json()
        self.assertTrue(villains and all(c["alignment"] == "villain" for c in villains))
        self.assertEqual(sum(self.client.get("/api/sides").get_json().values()), COUNT)

    def test_character_profile(self):
        first = self.client.get("/api/characters?q=Thor").get_json()[0]
        res = self.client.get(f"/api/characters/{first['id']}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["hero_name"], "Thor")

    def test_unknown_character_is_404(self):
        self.assertEqual(self.client.get("/api/characters/999").status_code, 404)

    def test_injection_attempt_is_harmless(self):
        res = self.client.get("/api/characters?q=' OR 1=1 --")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), [])


if __name__ == "__main__":
    unittest.main()
