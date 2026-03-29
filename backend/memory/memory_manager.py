"""
MemoryManager — unified interface for all 6 memory systems.

Agents call this rather than individual memory modules to keep
coupling low and make the memory architecture swappable.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional

from . import episodic, entity, procedural, semantic


# ── Conversation History helpers ─────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    db_path = os.getenv("SQLITE_DB_PATH", "./campaign_agent.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _ensure_conv_schema(conn)
    return conn


def _ensure_conv_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)"
    )
    conn.commit()


def save_message(session_id: str, role: str, content: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO conversations (session_id, role, content, created_at) VALUES (?,?,?,?)",
            (session_id, role, content, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_conversation_history(session_id: str, last_n: int = 10) -> list[dict[str, str]]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT role, content FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, last_n),
        ).fetchall()
    finally:
        conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# ── Unified load / save for graph nodes ──────────────────────────────────────

class MemoryManager:
    """
    Provides four key methods used by agent nodes:
        load_context()   — populate state with memory-retrieved context
        save_entities()  — extract + persist entities from user input
        save_episode()   — persist completed campaign as episodic memory
        get_snapshot()   — return dict of all memory stores for the UI
    """

    def load_context(
        self,
        session_id: str,
        product_name: str,
        campaign_goal: str,
        target_audience: str,
        current_agent_task: str,
    ) -> dict[str, str]:
        """
        Returns a dict with context strings ready to be merged into CampaignState.
        Called by the Orchestrator node before routing to specialised agents.
        """
        episodic_query = f"{product_name} {campaign_goal} {target_audience}"
        semantic_query = f"{campaign_goal} {current_agent_task} LinkedIn ads"
        procedural_query = current_agent_task

        return {
            "episodic_context": episodic.retrieve_similar_episodes(episodic_query),
            "semantic_context": semantic.retrieve_knowledge(semantic_query),
            "procedural_context": procedural.retrieve_procedures(procedural_query),
            "entities": entity.get_entities_for_session(session_id),
        }

    def save_entities(
        self,
        session_id: str,
        product_name: str,
        campaign_goal: str,
        target_audience: str,
        tone: str,
        budget: str,
        platforms: list[str],
    ) -> None:
        """Extract structured entities from user input and persist them."""
        entity.upsert_entity(session_id, "product", product_name)
        entity.upsert_entity(session_id, "campaign_goal", campaign_goal)
        entity.upsert_entity(session_id, "target_audience", target_audience)
        entity.upsert_entity(session_id, "tone", tone)
        entity.upsert_entity(session_id, "budget", budget)
        for p in platforms:
            entity.upsert_entity(session_id, "platform", p)

    def save_episode(
        self,
        session_id: str,
        product_name: str,
        campaign_goal: str,
        target_audience: str,
        campaign_plan: Optional[dict],
        ad_variants: list[dict],
        critic_score: Optional[dict],
        publish_result: Optional[dict] = None,
    ) -> None:
        episodic.store_episode(
            session_id=session_id,
            product_name=product_name,
            campaign_goal=campaign_goal,
            target_audience=target_audience,
            campaign_plan=campaign_plan or {},
            ad_variants=ad_variants,
            critic_score=critic_score or {},
            publish_result=publish_result,
        )

    def get_snapshot(self, session_id: str) -> dict[str, Any]:
        """Return all memory stores for the Memory Explorer UI endpoint."""
        return {
            "working": {},  # populated from live state by the API layer
            "episodic": _get_episodic_snapshot(session_id),
            "semantic": _get_semantic_snapshot(),
            "conversation": get_conversation_history(session_id, last_n=20),
            "entity": entity.get_entities_for_session(session_id),
            "procedural": _get_procedural_snapshot(),
        }


# ── Snapshot helpers for the UI ───────────────────────────────────────────────

def _get_episodic_snapshot(session_id: str) -> list[dict]:
    import chromadb
    from chromadb.utils import embedding_functions

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    try:
        client = chromadb.PersistentClient(path=persist_dir)
        ef = embedding_functions.DefaultEmbeddingFunction()
        col = client.get_or_create_collection("episodes", embedding_function=ef)
        if col.count() == 0:
            return []
        results = col.get(limit=10)
        return [
            {"id": i, "preview": d[:300] + "..." if len(d) > 300 else d, "metadata": m}
            for i, d, m in zip(
                results["ids"], results["documents"], results["metadatas"]
            )
        ]
    except Exception:
        return []


def _get_semantic_snapshot() -> list[dict]:
    import chromadb
    from chromadb.utils import embedding_functions

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    try:
        client = chromadb.PersistentClient(path=persist_dir)
        ef = embedding_functions.DefaultEmbeddingFunction()
        col = client.get_or_create_collection("knowledge", embedding_function=ef)
        if col.count() == 0:
            return []
        results = col.get(limit=20)
        return [
            {"id": i, "preview": d[:200] + "..." if len(d) > 200 else d}
            for i, d in zip(results["ids"], results["documents"])
        ]
    except Exception:
        return []


def _get_procedural_snapshot() -> list[dict]:
    import chromadb
    from chromadb.utils import embedding_functions

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    try:
        client = chromadb.PersistentClient(path=persist_dir)
        ef = embedding_functions.DefaultEmbeddingFunction()
        col = client.get_or_create_collection("procedures", embedding_function=ef)
        if col.count() == 0:
            return []
        results = col.get(limit=10)
        return [
            {"id": i, "preview": d[:200] + "..." if len(d) > 200 else d}
            for i, d in zip(results["ids"], results["documents"])
        ]
    except Exception:
        return []


memory_manager = MemoryManager()
