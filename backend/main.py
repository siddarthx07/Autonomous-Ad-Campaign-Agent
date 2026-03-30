"""
FastAPI backend for the Autonomous Campaign Agent.

Endpoints:
  POST /api/campaign/run      — Start a campaign run (returns session_id immediately)
  GET  /api/campaign/stream   — SSE stream of agent events for a session
  GET  /api/campaign/{id}     — Get final state of a completed campaign
  GET  /api/memory/{id}       — Get memory snapshot for the Memory Explorer UI
  GET  /api/health            — Health check
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

load_dotenv()

# In-memory session store: session_id → final CampaignState (or None if still running)
_sessions: dict[str, dict[str, Any] | None] = {}
# Event queues: session_id → asyncio.Queue of event dicts
_event_queues: dict[str, asyncio.Queue] = {}
# Session creation timestamps for TTL eviction
_session_timestamps: dict[str, float] = {}

# Sessions older than this are evicted from memory (keeps RAM bounded for demos)
_SESSION_TTL_SECONDS = 3 * 60 * 60  # 3 hours


def _evict_expired_sessions() -> None:
    """Remove sessions older than _SESSION_TTL_SECONDS."""
    import time
    cutoff = time.time() - _SESSION_TTL_SECONDS
    expired = [sid for sid, ts in _session_timestamps.items() if ts < cutoff]
    for sid in expired:
        _sessions.pop(sid, None)
        _event_queues.pop(sid, None)
        _session_timestamps.pop(sid, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly initialise ChromaDB collections (seeds knowledge + procedures)
    from memory.semantic import retrieve_knowledge
    from memory.procedural import retrieve_procedures
    from memory.memory_manager import load_campaigns_from_db
    retrieve_knowledge("init")
    retrieve_procedures("init")
    # Restore previously completed campaigns from SQLite so they survive restarts
    import time
    for sid, state in load_campaigns_from_db():
        _sessions[sid] = state
        _session_timestamps[sid] = time.time()  # treat as fresh for TTL purposes
    yield


app = FastAPI(
    title="Campaign Agent API",
    description="Autonomous multi-agent social media campaign system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class CampaignRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    product_description: str = Field(..., min_length=10, max_length=2000)
    product_url: Optional[str] = Field(default=None, description="Landing page URL for targeted research")
    usp: str = Field(default="", description="Unique selling proposition — the one thing that makes you different")
    cta_goal: str = Field(default="Learn More", description="Specific CTA e.g. Book a Demo, Start Free Trial")
    cta_link: str = Field(default="", description="URL the CTA points to — embedded in copy")
    campaign_goal: str = Field(..., description="e.g. brand awareness, lead generation")
    target_audience: str = Field(..., min_length=5, max_length=500)
    tone: str = Field(default="professional", description="e.g. professional, casual, bold")
    platforms: list[str] = Field(default=["linkedin", "twitter"])
    publish_mode: str = Field(default="now", description="now | scheduled | both")
    schedule_cadence: str = Field(default="daily_1", description="daily_1 | daily_2 | weekly | custom")
    custom_cadence: str = Field(default="", description="Free-text cadence description when schedule_cadence=custom")
    session_id: Optional[str] = Field(default=None)


class CampaignStartResponse(BaseModel):
    session_id: str
    message: str


# ── Background task: run the graph and stream events ─────────────────────────

async def _run_campaign(session_id: str, request: CampaignRequest) -> None:
    """
    Execute the LangGraph campaign pipeline once using astream (stream_mode="values").

    Each chunk is the full accumulated state after a node completes — the last
    chunk IS the final state, so we never need to call invoke() separately.
    This eliminates the previous double-execution bug.
    """
    from graph.campaign_graph import campaign_graph, make_initial_state

    queue = _event_queues[session_id]
    initial_state = make_initial_state(
        product_name=request.product_name,
        product_description=request.product_description,
        product_url=request.product_url,
        usp=request.usp,
        cta_goal=request.cta_goal,
        cta_link=request.cta_link,
        campaign_goal=request.campaign_goal,
        target_audience=request.target_audience,
        tone=request.tone,
        platforms=request.platforms,
        publish_mode=request.publish_mode,
        schedule_cadence=request.schedule_cadence,
        custom_cadence=request.custom_cadence,
        session_id=session_id,
    )

    await queue.put({
        "type": "start",
        "session_id": session_id,
        "message": "Campaign agent pipeline starting...",
    })

    seen_event_ids: set[str] = set()
    final_state: dict[str, Any] = {}

    try:
        # stream_mode="values" yields the complete state snapshot after each node.
        # No second invoke() needed — the last snapshot is the final state.
        async for state_snapshot in campaign_graph.astream(
            initial_state, stream_mode="values"
        ):
            final_state = state_snapshot

            # Forward any new agent events to the SSE queue
            for event in state_snapshot.get("events", []):
                eid = event.get("id", "")
                if eid not in seen_event_ids:
                    seen_event_ids.add(eid)
                    await queue.put({"type": "agent_event", "event": event})

        _sessions[session_id] = final_state
        # Persist to SQLite so the campaign survives server restarts
        from memory.memory_manager import save_campaign_to_db
        save_campaign_to_db(session_id, final_state)
        await queue.put({
            "type": "complete",
            "session_id": session_id,
            "status": final_state.get("status", "done"),
            "publish_result": final_state.get("publish_result"),
        })

    except Exception as exc:
        failed_state = {**final_state, "error": str(exc), "status": "failed"}
        _sessions[session_id] = failed_state
        from memory.memory_manager import save_campaign_to_db
        save_campaign_to_db(session_id, failed_state)
        await queue.put({
            "type": "error",
            "session_id": session_id,
            "error": str(exc),
        })
    finally:
        await queue.put(None)  # sentinel — closes the SSE stream


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "campaign-agent-api"}


@app.post("/api/campaign/run", response_model=CampaignStartResponse)
async def run_campaign(request: CampaignRequest):
    """
    Start an autonomous campaign run.
    Returns session_id immediately; stream progress via GET /api/campaign/stream?session_id=...
    """
    import time
    session_id = request.session_id or str(uuid.uuid4())
    _sessions[session_id] = None
    _event_queues[session_id] = asyncio.Queue()
    _session_timestamps[session_id] = time.time()

    # Evict sessions older than TTL to prevent unbounded memory growth
    _evict_expired_sessions()

    # Kick off graph in background
    asyncio.create_task(_run_campaign(session_id, request))

    return CampaignStartResponse(
        session_id=session_id,
        message="Campaign started. Connect to /api/campaign/stream to follow progress.",
    )


@app.get("/api/campaign/stream")
async def stream_campaign(session_id: str = Query(...)):
    """
    SSE endpoint: streams agent events for a running campaign.
    Each event is a JSON object with `type` and relevant fields.
    """
    if session_id not in _event_queues:
        raise HTTPException(status_code=404, detail="Session not found. Call /run first.")

    queue = _event_queues[session_id]

    async def event_generator() -> AsyncGenerator[dict, None]:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield {
                "data": json.dumps(item),
                "event": item.get("type", "message"),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/campaign/{session_id}")
async def get_campaign(session_id: str):
    """Get the final state of a completed campaign."""
    from memory.memory_manager import list_campaigns_summary

    state = _sessions.get(session_id)

    # Session not in memory at all → check SQLite campaigns table
    if state is None and session_id not in _sessions:
        db_rows = list_campaigns_summary()
        db_match = next((r for r in db_rows if r["session_id"] == session_id), None)
        if db_match:
            # Backfilled / lightweight row — return what we have from SQLite
            return {
                "session_id": session_id,
                "status": db_match.get("status", "published"),
                "product_name": db_match.get("product_name", ""),
                "campaign_goal": db_match.get("campaign_goal", ""),
                "campaign_plan": None,
                "ad_variants": [],
                "audience_segments": [],
                "critic_score": None,
                "publish_result": None,
                "task_plan": [],
                "research_findings": "",
                "events": [],
                "error": None,
            }
        raise HTTPException(status_code=404, detail="Session not found")

    # Session exists in memory but graph hasn't finished yet
    if state is None:
        return {"status": "running", "session_id": session_id}

    # Full state from a completed run — but if state_json was empty (backfill),
    # fall back to the campaigns table for the status field.
    resolved_status = state.get("status")
    if not resolved_status:
        db_rows = list_campaigns_summary()
        db_match = next((r for r in db_rows if r["session_id"] == session_id), None)
        resolved_status = db_match.get("status", "published") if db_match else "published"

    return {
        "session_id": session_id,
        "status": resolved_status,
        "product_name": state.get("product_name", ""),
        "campaign_goal": state.get("campaign_goal", ""),
        "campaign_plan": state.get("campaign_plan"),
        "ad_variants": state.get("ad_variants", []),
        "audience_segments": state.get("audience_segments", []),
        "critic_score": state.get("critic_score"),
        "publish_result": state.get("publish_result"),
        "task_plan": state.get("task_plan", []),
        "research_findings": state.get("research_findings", ""),
        "events": state.get("events", []),
        "error": state.get("error"),
    }


@app.get("/api/memory/{session_id}")
async def get_memory(session_id: str):
    """Return all memory stores for the Memory Explorer UI."""
    from memory.memory_manager import get_conversation_summary, memory_manager

    snapshot = memory_manager.get_snapshot(session_id)

    # Inject working memory from live session state if available
    live_state = _sessions.get(session_id)
    if live_state and isinstance(live_state, dict):
        snapshot["working"] = {
            "task_plan": live_state.get("task_plan", []),
            "orchestrator_notes": live_state.get("orchestrator_notes", ""),
            "revision_count": live_state.get("revision_count", 0),
            "status": live_state.get("status", "running"),
            "conversation_summary_preview": get_conversation_summary(session_id)[:300],
            "research_findings_preview": (live_state.get("research_findings", ""))[:300],
        }

    return snapshot


@app.get("/api/campaign/{session_id}/analytics")
async def get_campaign_analytics(session_id: str, refresh: bool = False):
    """
    Return engagement metrics for posts published by a campaign.

    Strategy:
    1. Serve SQLite cache unless refresh=True.
    2. If publish_result has specific post IDs → fetch those from Buffer.
    3. Fallback: query Buffer channels directly for recent sent posts
       (handles backfilled campaigns whose state_json is empty).
    """
    from memory.memory_manager import (
        load_performance_metrics,
        save_performance_metrics,
        list_campaigns_summary,
    )
    from tools.buffer_tool import fetch_post_analytics, fetch_channel_posts

    # ── 1. Serve cache ──────────────────────────────────────────────────────
    if not refresh:
        cached = load_performance_metrics(session_id)
        if cached:
            return {"session_id": session_id, "metrics": cached, "source": "cache"}

    # ── 2. Verify campaign exists ───────────────────────────────────────────
    db_rows = list_campaigns_summary()
    db_match = next((r for r in db_rows if r["session_id"] == session_id), None)
    if session_id not in _sessions and not db_match:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # ── 3. Try specific post IDs from publish_result ────────────────────────
    state = _sessions.get(session_id) or {}
    # For campaigns loaded from SQLite at startup, state may be a full dict
    publish_result = state.get("publish_result") or {}
    linkedin_ids: list[str] = publish_result.get("linkedin_ids") or []
    twitter_ids: list[str] = publish_result.get("twitter_ids") or []

    metrics: list[dict] = []

    if linkedin_ids or twitter_ids:
        for post_id in linkedin_ids:
            result = fetch_post_analytics(post_id)
            result["platform"] = "linkedin"
            metrics.append(result)
        for post_id in twitter_ids:
            result = fetch_post_analytics(post_id)
            result["platform"] = "twitter"
            metrics.append(result)
    else:
        # ── 4. Fallback: pull recent posts directly from Buffer channels ────
        channel_ids = []
        linkedin_ch = os.getenv("BUFFER_LINKEDIN_CHANNEL_ID", "").strip()
        twitter_ch = os.getenv("BUFFER_TWITTER_CHANNEL_ID", "").strip()
        if linkedin_ch:
            channel_ids.append(linkedin_ch)
        if twitter_ch:
            channel_ids.append(twitter_ch)

        if channel_ids:
            metrics.extend(fetch_channel_posts(channel_ids, limit=5))

    # ── 5. Cache valid results ──────────────────────────────────────────────
    valid = [m for m in metrics if "error" not in m]
    if valid:
        save_performance_metrics(session_id, valid)

    return {"session_id": session_id, "metrics": metrics, "source": "live"}


@app.get("/api/sessions")
async def list_sessions():
    """
    List all campaigns for the dashboard.

    Reads from SQLite for completed/failed campaigns (persisted across restarts)
    and overlays any currently-running in-memory sessions on top.
    """
    from memory.memory_manager import list_campaigns_summary

    # Start from persisted campaigns (newest first)
    db_rows = list_campaigns_summary()
    db_ids = {r["session_id"] for r in db_rows}

    # Add any live sessions not yet flushed to SQLite (still running)
    running = []
    for sid, state in _sessions.items():
        if sid not in db_ids and state is None:
            running.append({
                "session_id": sid,
                "status": "running",
                "product_name": "",
                "campaign_goal": "",
                "created_at": None,
            })

    return {"sessions": running + db_rows}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
