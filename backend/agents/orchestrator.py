"""
Orchestrator Agent — GPT-4o

Responsibilities:
  1. Load all relevant memories into state (episodic, semantic, procedural, entity).
  2. Extract and persist entities from user input.
  3. Generate a structured task plan for the campaign.
  4. Emit an SSE event summarising its analysis.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import CampaignState
from memory.memory_manager import memory_manager, save_message
from memory.episodic import extract_campaign_lessons

_llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

_SYSTEM = """You are the Orchestrator of an autonomous marketing campaign AI system.
Your role is to:
1. Analyse the user's campaign brief.
2. Create a clear, ordered task plan for the campaign agents.
3. Identify key constraints and success criteria.

Respond with a JSON object:
{{
  "task_plan": ["step 1", "step 2", ...],
  "notes": "brief orchestrator commentary",
  "entities": {{
    "brand": "...",
    "product": "...",
    "persona_summary": "..."
  }}
}}
"""


def orchestrator_node(state: CampaignState) -> dict:
    """LangGraph node: loads memory, creates task plan, seeds entity store."""
    session_id = state["session_id"]

    # Persist user turn to conversation history
    usp_line = f"USP: {state['usp']}\n" if state.get("usp") else ""
    url_line = f"Landing Page: {state['product_url']}\n" if state.get("product_url") else ""
    user_brief = (
        f"Product: {state['product_name']}\n"
        f"Description: {state['product_description']}\n"
        f"{url_line}"
        f"{usp_line}"
        f"CTA Goal: {state['cta_goal']}\n"
        f"Goal: {state['campaign_goal']}\n"
        f"Audience: {state['target_audience']}\n"
        f"Tone: {state['tone']}\n"
        f"Platforms: {', '.join(state['platforms'])}"
    )
    save_message(session_id, "user", user_brief)

    # Save structured entities to Entity Memory
    memory_manager.save_entities(
        session_id=session_id,
        product_name=state["product_name"],
        campaign_goal=state["campaign_goal"],
        target_audience=state["target_audience"],
        tone=state["tone"],
        platforms=state["platforms"],
    )

    # Load all memory context
    mem_ctx = memory_manager.load_context(
        session_id=session_id,
        product_name=state["product_name"],
        campaign_goal=state["campaign_goal"],
        target_audience=state["target_audience"],
        current_agent_task="campaign orchestration and planning",
    )

    # Extract distilled lessons from past similar episodes (the real learning step)
    lesson_query = f"{state['campaign_goal']} {state['target_audience']} {state['tone']}"
    lessons = extract_campaign_lessons(lesson_query)

    prompt = (
        f"Campaign Brief:\n{user_brief}\n\n"
        f"Lessons From Past Campaigns:\n{lessons['lesson_summary']}\n\n"
        f"Past Similar Campaigns (Episodic Memory):\n{mem_ctx['episodic_context']}\n\n"
        f"Platform Knowledge (Semantic Memory):\n{mem_ctx['semantic_context'][:800]}"
    )

    response = _llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])

    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}

    task_plan = parsed.get("task_plan", [
        "Research market and competitors",
        "Build campaign strategy",
        "Generate ad copy variants",
        "Define audience targeting",
        "Critique and refine content",
        "Publish to LinkedIn and Buffer",
    ])
    notes = parsed.get("notes", "")

    # Include lessons in the event so the frontend/results page can display them
    lessons_content = lessons["lesson_summary"]
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "orchestrator",
        "type": "analysis",
        "title": "Campaign Brief Analysed",
        "content": (
            f"Task plan created with {len(task_plan)} steps.\n{notes}\n\n"
            f"Lessons applied:\n{lessons_content}"
        ),
        "memory_reads": ["episodic", "semantic", "entity"],
        "data": {"lessons": lessons},
    }

    save_message(session_id, "assistant", f"Orchestrator: {notes}")

    return {
        "task_plan": task_plan,
        "orchestrator_notes": notes,
        "episodic_context": mem_ctx["episodic_context"],
        "campaign_lessons": lessons,
        "semantic_context": mem_ctx["semantic_context"],
        "procedural_context": mem_ctx["procedural_context"],
        "entities": mem_ctx["entities"],
        "messages": state.get("messages", []) + [{"role": "user", "content": user_brief}],
        "events": state.get("events", []) + [event],
        "status": "running",
    }
