"""Writes marvel.db to disk so you can explore it with sqlite3 or DB Browser."""
from pathlib import Path
from app import db

if __name__ == "__main__":
    Path("marvel.db").unlink(missing_ok=True)   # rebuild from scratch each time
    conn = db.build(db.connect("marvel.db"))
    count = conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    print(f"Built marvel.db with {count} characters")
