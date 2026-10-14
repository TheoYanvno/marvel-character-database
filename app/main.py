"""Flask web app: JSON API + single-page front end."""
import os
from flask import Flask, jsonify, render_template, request, abort

from app import db

app = Flask(__name__)
conn = db.build(db.connect())     # in-memory database rebuilt from data/ on start


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/characters")
def list_characters():
    return jsonify(db.search(conn, request.args.get("q", "")))


@app.get("/api/characters/<int:character_id>")
def character(character_id):
    profile = db.get_character(conn, character_id)
    if profile is None:
        abort(404)
    return jsonify(profile)


@app.get("/api/stats")
def stats():
    return jsonify(db.stats(conn))


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)
