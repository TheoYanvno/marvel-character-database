-- Marvel Character Database schema (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE characters (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  hero_name        TEXT NOT NULL UNIQUE,
  real_name        TEXT,
  alignment        TEXT NOT NULL CHECK (alignment IN ('hero', 'villain', 'antihero')),
  first_appearance TEXT NOT NULL,          -- comic issue
  first_year       INTEGER NOT NULL,
  creators         TEXT NOT NULL,
  origin           TEXT NOT NULL,
  color            TEXT NOT NULL           -- card accent color
);

CREATE TABLE powers (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  name  TEXT NOT NULL UNIQUE
);

-- many-to-many: a character has many powers, a power belongs to many characters
CREATE TABLE character_powers (
  character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  power_id     INTEGER NOT NULL REFERENCES powers(id),
  PRIMARY KEY (character_id, power_id)
);

CREATE TABLE teams (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  name  TEXT NOT NULL UNIQUE
);

CREATE TABLE character_teams (
  character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  team_id      INTEGER NOT NULL REFERENCES teams(id),
  PRIMARY KEY (character_id, team_id)
);

-- related_id is set when the related person is also in the database
CREATE TABLE relationships (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  character_id  INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  related_name  TEXT NOT NULL,
  related_id    INTEGER REFERENCES characters(id),
  kind          TEXT NOT NULL CHECK (kind IN ('family', 'ally', 'romance', 'mentor', 'enemy'))
);

CREATE TABLE appearances (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  character_id  INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  medium        TEXT NOT NULL CHECK (medium IN ('comic', 'film', 'tv', 'animation', 'game')),
  title         TEXT NOT NULL,
  year          INTEGER NOT NULL,
  note          TEXT
);

CREATE INDEX idx_relationships_character ON relationships(character_id);
CREATE INDEX idx_appearances_character   ON appearances(character_id);
