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
    retrieve_knowledge("init")
    retrieve_procedures("init")
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
    campaign_goal: str = Field(..., description="e.g. brand awareness, lead generation")
    target_audience: str = Field(..., min_length=5, max_length=500)
    tone: str = Field(default="professional", description="e.g. professional, casual, bold")
    budget: str = Field(default="$500/week")
    platforms: list[str] = Field(default=["linkedin", "twitter"])
    publish_mode: str = Field(default="now", description="now | scheduled | both")
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
        campaign_goal=request.campaign_goal,
        target_audience=request.target_audience,
        tone=request.tone,
        budget=request.budget,
        platforms=request.platforms,
        publish_mode=request.publish_mode,
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
        await queue.put({
            "type": "complete",
            "session_id": session_id,
            "status": final_state.get("status", "done"),
            "publish_result": final_state.get("publish_result"),
        })

    except Exception as exc:
        _sessions[session_id] = {**final_state, "error": str(exc), "status": "failed"}
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
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = _sessions[session_id]
    if state is None:
        return {"status": "running", "session_id": session_id}

    return {
        "session_id": session_id,
        "status": state.get("status"),
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
    from memory.memory_manager import memory_manager

    snapshot = memory_manager.get_snapshot(session_id)

    # Inject working memory from live session state if available
    live_state = _sessions.get(session_id)
    if live_state and isinstance(live_state, dict):
        snapshot["working"] = {
            "task_plan": live_state.get("task_plan", []),
            "orchestrator_notes": live_state.get("orchestrator_notes", ""),
            "revision_count": live_state.get("revision_count", 0),
            "status": live_state.get("status", "running"),
            "research_findings_preview": (live_state.get("research_findings", ""))[:300],
        }

    return snapshot


@app.get("/api/sessions")
async def list_sessions():
    """List all session IDs (for the dashboard)."""
    sessions = []
    for sid, state in _sessions.items():
        if state:
            sessions.append({
                "session_id": sid,
                "status": state.get("status", "unknown"),
                "product_name": state.get("product_name", ""),
                "campaign_goal": state.get("campaign_goal", ""),
                "published_at": state.get("publish_result", {}).get("published_at") if state.get("publish_result") else None,
            })
    return {"sessions": sessions}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
