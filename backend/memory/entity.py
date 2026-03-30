"""
Entity Memory — SQLite `entities` table.

Structured store of named entities extracted from conversations:
brands, products, personas, tones. Deduped by type + name.
Provides persistence across sessions so the agent remembers known entities.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any


def _get_conn() -> sqlite3.Connection:
    db_path = os.getenv("SQLITE_DB_PATH", "./campaign_agent.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            entity_type TEXT NOT NULL,   -- brand | product | persona | tone | platform
            name        TEXT NOT NULL,
            attributes  TEXT,            -- JSON blob of extra attributes
            created_at  TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entities_session ON entities(session_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)"
    )
    conn.commit()


def upsert_entity(
    session_id: str,
    entity_type: str,
    name: str,
    attributes: dict[str, Any] | None = None,
) -> None:
    """Insert or update an entity. Uses (session_id, entity_type, name) as natural key."""
    conn = _get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM entities WHERE session_id=? AND entity_type=? AND name=?",
            (session_id, entity_type, name),
        ).fetchone()

        attrs_json = json.dumps(attributes or {})
        now = datetime.utcnow().isoformat()

        if existing:
            conn.execute(
                "UPDATE entities SET attributes=? WHERE id=?",
                (attrs_json, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO entities (session_id, entity_type, name, attributes, created_at) VALUES (?,?,?,?,?)",
                (session_id, entity_type, name, attrs_json, now),
            )
        conn.commit()
    finally:
        conn.close()


def get_entities_for_session(session_id: str) -> dict[str, list[dict[str, Any]]]:
    """Return all entities for a session grouped by type."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT entity_type, name, attributes FROM entities WHERE session_id=?",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()

    result: dict[str, list[dict]] = {}
    for row in rows:
        etype = row["entity_type"]
        result.setdefault(etype, []).append(
            {"name": row["name"], "attributes": json.loads(row["attributes"] or "{}")}
        )
    return result


def format_entities_for_prompt(session_id: str) -> str:
    """Format entity memory as a readable block to inject into prompts."""
    entities = get_entities_for_session(session_id)
    if not entities:
        return "No entities stored yet."

    lines = ["Known entities from this session:"]
    for etype, items in entities.items():
        names = ", ".join(i["name"] for i in items)
        lines.append(f"  {etype.capitalize()}: {names}")
    return "\n".join(lines)
