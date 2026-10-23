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
  color            TEXT NOT NULL,          -- card accent color
  mcu_actor        TEXT,                   -- who plays them in the Marvel Cinematic Universe
  mcu_lore         TEXT,                   -- their story in the MCU
  mcu_note         TEXT,                   -- set instead when they haven't appeared in the MCU yet
  image            TEXT,                   -- optional photo for the card: a file name in app/static/images/
  image_credit     TEXT                    -- who the photo is by / where it's from, shown on the profile
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

-- related_id is set when the related person is also in the database.
-- Each pair is stored once; the profile query shows it on both characters' pages.
CREATE TABLE relationships (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  character_id  INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  related_name  TEXT NOT NULL,
  related_id    INTEGER REFERENCES characters(id),
  kind          TEXT NOT NULL CHECK (kind IN ('family', 'friend', 'romantic', 'enemy')),
  detail        TEXT CHECK (detail IN ('mentor', 'protégé', 'best friend', 'cousin', 'twin', 'married'))
);

CREATE TABLE appearances (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  character_id  INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  medium        TEXT NOT NULL CHECK (medium IN ('comic', 'film', 'tv', 'animation', 'game')),
  title         TEXT NOT NULL,
  year          INTEGER NOT NULL,
  note          TEXT
);

-- Marvel Cinematic Universe movies and series (live action)
CREATE TABLE mcu_titles (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,   -- ids follow release order
  title  TEXT NOT NULL UNIQUE,
  year   INTEGER NOT NULL,
  kind   TEXT NOT NULL CHECK (kind IN ('film', 'series'))
);

-- many-to-many: which characters appear in which MCU titles.
-- year is only set when it differs from the title's year (a later season of a series).
CREATE TABLE mcu_roles (
  character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  title_id     INTEGER NOT NULL REFERENCES mcu_titles(id),
  year         INTEGER,
  PRIMARY KEY (character_id, title_id)
);

CREATE INDEX idx_relationships_character ON relationships(character_id);
CREATE INDEX idx_appearances_character   ON appearances(character_id);
CREATE INDEX idx_mcu_roles_title         ON mcu_roles(title_id);
