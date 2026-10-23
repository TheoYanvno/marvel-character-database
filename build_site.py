"""Builds the live demo into docs/ for GitHub Pages.

GitHub Pages only serves static files, so instead of running Flask this script:
  1. builds the SQLite database (docs/marvel.db) with the same code the app uses,
  2. renders the page template and copies the front end and the card photos in use,
  3. copies sql/app_queries.sql, which the browser runs against marvel.db with sql.js.

Run it after changing data/characters.json, the SQL, or the front end:
    python build_site.py
"""
import shutil
from pathlib import Path

from flask import render_template

from app import db
from app.main import app

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"


def build(out=OUT):
    out = Path(out)
    out.mkdir(exist_ok=True)
    database = out / "marvel.db"
    database.unlink(missing_ok=True)
    conn = db.build(db.connect(str(database)))
    conn.execute("VACUUM")                      # smallest possible file to download
    conn.close()

    with app.test_request_context():
        (out / "index.html").write_text(render_template("index.html", static_site=True))
    for name in ("app.js", "static-api.js", "style.css"):
        shutil.copy(ROOT / "app" / "static" / name, out / name)
    shutil.copy(ROOT / "sql" / "app_queries.sql", out / "app_queries.sql")
    shutil.rmtree(out / "images", ignore_errors=True)   # card photos (only the ones in use are copied)
    used = {r["image"] for r in db.search(db.build(db.connect()), "") if r["image"]}
    (out / "images").mkdir()
    for name in used:
        shutil.copy(ROOT / "app" / "static" / "images" / name, out / "images" / name)
    (out / ".nojekyll").touch()                 # serve files as-is
    print(f"Built the live demo in {out}/")


if __name__ == "__main__":
    build()
