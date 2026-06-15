-- dnd_gm_assist prototype schema (SQLite). Fictional campaign data only.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS campaigns (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  name             TEXT NOT NULL,
  system           TEXT DEFAULT 'D&D 5e',
  setting          TEXT,
  tone             TEXT,                -- 'dark & gritty', 'heroic', 'whimsical', ...
  party_level      INTEGER DEFAULT 1,
  current_location TEXT,
  recent_events    TEXT,                -- rolling summary the DM keeps current
  known_npcs       TEXT,                -- free text: names, roles, secrets
  created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per AI generation (the session log / history).
CREATE TABLE IF NOT EXISTS generations (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_id  INTEGER NOT NULL REFERENCES campaigns(id),
  created_at   TEXT NOT NULL DEFAULT (datetime('now')),
  kind         TEXT NOT NULL,           -- encounter | loot | npc | description | note
  source       TEXT NOT NULL DEFAULT 'ai',  -- 'ai' | 'dm'
  dm_input     TEXT,                    -- what the DM described / asked
  title        TEXT,
  content      TEXT,                    -- the read-aloud / main text
  mechanic     TEXT,                    -- dice, DCs, stats (may be empty)
  secret       TEXT,                    -- DM-only twist (may be empty)
  connects_to  TEXT,                    -- tie-in to NPCs / events (may be empty)
  is_favorite  INTEGER DEFAULT 0
);

-- synthetic seed: one sample campaign
INSERT INTO campaigns (name, system, setting, tone, party_level, current_location, recent_events, known_npcs) VALUES
  ('The Obsidian Key', 'D&D 5e', 'Swamp-bound frontier of a fallen kingdom', 'dark & gritty', 5,
   'The Whispering Swamps',
   'Defeated the swamp-witch; recovered a glowing obsidian key whose purpose is unknown.',
   'Bryn - the witch''s former captive, secretly a cultist spy. Captain Hollow - a deserter who knows the key''s origin.');
