import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gm_assist.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")

_EDITABLE_FIELDS = {
    "name", "system", "setting", "tone", "party_level",
    "current_location", "recent_events", "known_npcs",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(SCHEMA_PATH, "r") as f:
            schema = f.read()
        conn = _connect()
        try:
            conn.executescript(schema)
            conn.commit()
        finally:
            conn.close()
    _migrate()


def _migrate() -> None:
    conn = _connect()
    try:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(generations)").fetchall()}
        if "source" not in existing:
            conn.execute("ALTER TABLE generations ADD COLUMN source TEXT NOT NULL DEFAULT 'ai'")
            conn.commit()
    finally:
        conn.close()


def list_campaigns() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, name, system FROM campaigns ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_campaign(fields: dict) -> dict:
    allowed = {k: v for k, v in fields.items() if k in _EDITABLE_FIELDS and v is not None}
    cols = list(allowed.keys())
    values = list(allowed.values())
    conn = _connect()
    try:
        cur = conn.execute(
            f"INSERT INTO campaigns ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            values,
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_campaign(campaign_id: int) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_campaign(campaign_id: int, fields: dict) -> dict | None:
    allowed = {k: v for k, v in fields.items() if k in _EDITABLE_FIELDS}
    if not allowed:
        return get_campaign(campaign_id)
    set_clause = ", ".join(f"{k} = ?" for k in allowed)
    values = list(allowed.values()) + [campaign_id]
    conn = _connect()
    try:
        conn.execute(
            f"UPDATE campaigns SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_generation(gen: dict) -> dict:
    cols = ("campaign_id", "kind", "source", "dm_input", "title", "content",
            "mechanic", "secret", "connects_to")
    values = tuple(gen.get(c, "ai") if c == "source" else gen.get(c) for c in cols)
    conn = _connect()
    try:
        cur = conn.execute(
            f"INSERT INTO generations ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            values,
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM generations WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def save_note(campaign_id: int, content: str) -> dict:
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO generations (campaign_id, kind, source, content) VALUES (?, 'note', 'dm', ?)",
            (campaign_id, content),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM generations WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_log(campaign_id: int) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM generations WHERE campaign_id = ? ORDER BY created_at DESC",
            (campaign_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
