"""
MemoryManager — unified interface for all 6 memory systems.

Agents call this rather than individual memory modules to keep
coupling low and make the memory architecture swappable.
"""
from __future__ import annotations

import json
import os
import re
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
    _ensure_conv_summary_schema(conn)
    _ensure_campaigns_schema(conn)
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


def _ensure_conv_summary_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            session_id       TEXT PRIMARY KEY,
            summary          TEXT NOT NULL,
            last_message_id  INTEGER NOT NULL,
            message_count    INTEGER NOT NULL,
            updated_at       TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _ensure_campaigns_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            session_id   TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            campaign_goal TEXT NOT NULL,
            status       TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            state_json   TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            post_id     TEXT NOT NULL,
            platform    TEXT NOT NULL,
            clicks      INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            reach       INTEGER DEFAULT 0,
            likes       INTEGER DEFAULT 0,
            comments    INTEGER DEFAULT 0,
            shares      INTEGER DEFAULT 0,
            text_preview TEXT,
            fetched_at  TEXT NOT NULL,
            UNIQUE(session_id, post_id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_perf_session ON performance_metrics(session_id)"
    )
    conn.commit()


def save_campaign_to_db(session_id: str, state: dict) -> None:
    """Persist a completed campaign state to SQLite so it survives restarts."""
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO campaigns
                (session_id, product_name, campaign_goal, status, created_at, state_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                state.get("product_name", ""),
                state.get("campaign_goal", ""),
                state.get("status", "unknown"),
                datetime.utcnow().isoformat(),
                json.dumps(state),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def load_campaigns_from_db() -> list[dict]:
    """Load all persisted campaigns from SQLite (called on server startup)."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT session_id, state_json FROM campaigns ORDER BY created_at DESC"
        ).fetchall()
        result = []
        for row in rows:
            try:
                result.append((row["session_id"], json.loads(row["state_json"])))
            except (json.JSONDecodeError, KeyError):
                pass
        return result
    finally:
        conn.close()


def list_campaigns_summary() -> list[dict]:
    """Return lightweight summaries of all campaigns for the dashboard."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """
            SELECT session_id, product_name, campaign_goal, status, created_at
            FROM campaigns
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_performance_metrics(session_id: str, metrics: list[dict]) -> None:
    """Upsert per-post engagement stats returned from Buffer analytics."""
    conn = _get_conn()
    try:
        for m in metrics:
            conn.execute(
                """
                INSERT INTO performance_metrics
                    (session_id, post_id, platform, clicks, impressions, reach,
                     likes, comments, shares, text_preview, fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(session_id, post_id) DO UPDATE SET
                    clicks=excluded.clicks,
                    impressions=excluded.impressions,
                    reach=excluded.reach,
                    likes=excluded.likes,
                    comments=excluded.comments,
                    shares=excluded.shares,
                    text_preview=excluded.text_preview,
                    fetched_at=excluded.fetched_at
                """,
                (
                    session_id,
                    m.get("post_id", ""),
                    m.get("platform", ""),
                    m.get("clicks", 0),
                    m.get("impressions", 0),
                    m.get("reach", 0),
                    m.get("likes", 0),
                    m.get("comments", 0),
                    m.get("shares", 0),
                    m.get("text_preview", ""),
                    datetime.utcnow().isoformat(),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def load_performance_metrics(session_id: str) -> list[dict]:
    """Load cached per-post engagement stats for a campaign."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """
            SELECT post_id, platform, clicks, impressions, reach,
                   likes, comments, shares, text_preview, fetched_at
            FROM performance_metrics
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


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

    try:
        update_conversation_summary(session_id)
    except Exception:
        # Summary maintenance should never block the main campaign flow.
        pass


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


def _clip_text(text: str, max_chars: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3] + "..."


def _fallback_conversation_summary(
    existing_summary: str,
    new_rows: list[sqlite3.Row],
) -> str:
    combined_blocks = [existing_summary] if existing_summary else []
    combined_blocks.extend(str(row["content"] or "") for row in new_rows)

    lines = [
        line.strip()
        for block in combined_blocks
        for line in block.splitlines()
        if line.strip()
    ]

    def _existing_section_items(heading: str) -> list[str]:
        if not existing_summary:
            return []
        match = re.search(
            rf"{re.escape(heading)}:\n(.*?)(?:\n\n[A-Z][A-Za-z ]+:\n|\Z)",
            existing_summary,
            re.DOTALL,
        )
        if not match:
            return []
        body = match.group(1).strip()
        if not body or body == "None recorded." or body == "Conversation just started.":
            return []
        return [
            line.lstrip("- ").strip()
            for line in body.splitlines()
            if line.strip()
        ]
    lower_field_names = {
        "product",
        "description",
        "goal",
        "audience",
        "tone",
        "platforms",
        "cta goal",
        "cta link",
        "landing page",
        "usp",
    }

    def _latest_field(label: str) -> str:
        prefix = f"{label.lower()}:"
        for line in reversed(lines):
            if line.lower().startswith(prefix):
                return line.split(":", 1)[1].strip()
        return ""

    brief_parts = []
    product = _latest_field("product")
    goal = _latest_field("goal")
    audience = _latest_field("audience")
    tone = _latest_field("tone")
    platforms = _latest_field("platforms")
    cta_goal = _latest_field("cta goal")
    if product:
        brief_parts.append(f"Product: {product}")
    if goal:
        brief_parts.append(f"Goal: {goal}")
    if audience:
        brief_parts.append(f"Audience: {audience}")
    if tone:
        brief_parts.append(f"Tone: {tone}")
    if platforms:
        brief_parts.append(f"Platforms: {platforms}")
    if cta_goal:
        brief_parts.append(f"CTA: {cta_goal}")

    preferences: list[str] = _existing_section_items("Constraints And Preferences")
    progress: list[str] = _existing_section_items("Progress And Decisions")
    open_items: list[str] = _existing_section_items("Open Items")

    for row in new_rows[-8:]:
        role = str(row["role"] or "").lower()
        content = str(row["content"] or "")
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if ":" in line and line.split(":", 1)[0].strip().lower() in lower_field_names:
                continue
            clipped = _clip_text(line, 180)
            lower = line.lower()
            if role == "assistant":
                progress.append(clipped)
            elif any(word in lower for word in ["avoid", "prefer", "prioritize", "must", "focus", "stronger"]):
                preferences.append(clipped)
            elif "?" in line:
                open_items.append(clipped)
            else:
                progress.append(clipped)

    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    preferences = _dedupe(preferences)
    progress = _dedupe(progress)
    open_items = _dedupe(open_items)

    sections = [
        "Campaign Brief:\n" + ("; ".join(brief_parts) if brief_parts else "Summary not established yet."),
        "Constraints And Preferences:\n" + ("\n".join(f"- {p}" for p in preferences[:4]) if preferences else "None recorded."),
        "Progress And Decisions:\n" + ("\n".join(f"- {p}" for p in progress[:4]) if progress else "Conversation just started."),
        "Open Items:\n" + ("\n".join(f"- {p}" for p in open_items[:3]) if open_items else "None recorded."),
    ]
    return "\n\n".join(sections).strip()


def _summarize_conversation_increment(
    existing_summary: str,
    new_rows: list[sqlite3.Row],
) -> str:
    if not new_rows:
        return existing_summary

    fallback = _fallback_conversation_summary(existing_summary, new_rows)
    formatted_messages = "\n\n".join(
        f"{row['role'].upper()}:\n{_clip_text(row['content'], 700)}"
        for row in new_rows
    )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except Exception:
        return fallback

    system_prompt = (
        "You maintain a rolling conversation-memory summary for a multi-agent "
        "marketing system. Update the summary using the new messages.\n\n"
        "Keep it concise and durable. Prefer stable facts and decisions over "
        "verbatim phrasing. Capture:\n"
        "- product, audience, goal, CTA, platforms\n"
        "- constraints, preferences, and notable changes\n"
        "- progress/status updates from the assistant\n"
        "- unresolved questions or missing inputs\n\n"
        "Return plain text only using exactly these headings:\n"
        "Campaign Brief:\n"
        "Constraints And Preferences:\n"
        "Progress And Decisions:\n"
        "Open Items:\n"
        "Keep the full summary under 220 words."
    )
    human_prompt = (
        f"Existing summary:\n{existing_summary or 'None yet.'}\n\n"
        f"New messages to incorporate:\n{formatted_messages}"
    )

    try:
        llm = ChatOpenAI(
            model=os.getenv("CONVERSATION_SUMMARY_MODEL", "gpt-4o-mini"),
            temperature=0.1,
        )
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        )
        summary = (response.content or "").strip()
        return summary or fallback
    except Exception:
        return fallback


def update_conversation_summary(session_id: str) -> str:
    conn = _get_conn()
    try:
        existing = conn.execute(
            """
            SELECT summary, last_message_id, message_count
            FROM conversation_summaries
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        last_message_id = int(existing["last_message_id"]) if existing else 0
        existing_summary = existing["summary"] if existing else ""

        new_rows = conn.execute(
            """
            SELECT id, role, content
            FROM conversations
            WHERE session_id = ? AND id > ?
            ORDER BY id ASC
            """,
            (session_id, last_message_id),
        ).fetchall()
        if not new_rows:
            return existing_summary

        total_messages = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    updated_summary = _summarize_conversation_increment(existing_summary, new_rows)
    last_seen_id = int(new_rows[-1]["id"])
    now = datetime.utcnow().isoformat()

    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT INTO conversation_summaries
                (session_id, summary, last_message_id, message_count, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                summary = excluded.summary,
                last_message_id = excluded.last_message_id,
                message_count = excluded.message_count,
                updated_at = excluded.updated_at
            """,
            (session_id, updated_summary, last_seen_id, total_messages, now),
        )
        conn.commit()
    finally:
        conn.close()

    return updated_summary


def get_conversation_summary(session_id: str) -> str:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT summary FROM conversation_summaries WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row["summary"] if row else ""
    finally:
        conn.close()


def get_conversation_context(session_id: str, recent_n: int = 4) -> str:
    summary = update_conversation_summary(session_id)
    recent_messages = get_conversation_history(session_id, last_n=recent_n)

    if not summary and not recent_messages:
        return "No conversation context yet."

    recent_block = "\n".join(
        f"{msg['role'].upper()}: {_clip_text(msg['content'], 240)}"
        for msg in recent_messages
    )
    blocks: list[str] = []
    if summary:
        blocks.append(f"Conversation summary:\n{summary}")
    if recent_block:
        blocks.append(f"Recent turns:\n{recent_block}")
    return "\n\n".join(blocks)


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
            "conversation_context": get_conversation_context(session_id),
            "entities": entity.get_entities_for_session(session_id),
        }

    def save_entities(
        self,
        session_id: str,
        product_name: str,
        campaign_goal: str,
        target_audience: str,
        tone: str,
        platforms: list[str],
    ) -> None:
        """Extract structured entities from user input and persist them."""
        entity.upsert_entity(session_id, "product", product_name)
        entity.upsert_entity(session_id, "campaign_goal", campaign_goal)
        entity.upsert_entity(session_id, "target_audience", target_audience)
        entity.upsert_entity(session_id, "tone", tone)
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
