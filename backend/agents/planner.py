"""
Planning Agent — GPT-4o

Generates a full campaign strategy:
  - Objectives and KPIs
  - Timeline
  - Platform mix and rationale
  - Messaging pillars
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import CampaignState, CampaignPlan
from memory.procedural import retrieve_procedures
from memory.semantic import retrieve_knowledge

_llm = ChatOpenAI(model="gpt-4o", temperature=0.5)

_SYSTEM = """You are a senior marketing strategist specialising in B2B digital campaigns.
Given a campaign brief and relevant context, produce a detailed campaign strategy.

Respond with a JSON object:
{{
  "objective": "one clear sentence",
  "kpis": ["KPI 1", "KPI 2", "KPI 3"],
  "timeline": "e.g. 4-week sprint: Week 1 launch, Week 2–3 optimise, Week 4 analyse",
  "platforms": ["linkedin", "buffer"],
  "messaging_pillars": ["pillar 1", "pillar 2", "pillar 3"],
  "strategy_summary": "2-3 sentence overview"
}}
"""


def planner_node(state: CampaignState) -> dict:
    """LangGraph node: generates structured campaign plan."""

    # Pull procedural SOPs relevant to campaign planning
    sop = retrieve_procedures("campaign planning strategy")
    knowledge = retrieve_knowledge(f"{state['campaign_goal']} campaign strategy LinkedIn")

    lessons = state.get("campaign_lessons") or {}
    lessons_block = lessons.get("lesson_summary", "No past lessons available.")

    prompt = (
        f"Product: {state['product_name']}\n"
        f"Description: {state['product_description']}\n"
        f"Goal: {state['campaign_goal']}\n"
        f"Target Audience: {state['target_audience']}\n"
        f"Tone: {state['tone']}\n"
        f"Conversation Memory:\n{state.get('conversation_context', '')}\n\n"
        f"Platforms: {', '.join(state['platforms'])}\n\n"
        f"Learned Lessons From Past Campaigns (use these to guide strategy):\n{lessons_block}\n\n"
        f"Procedural SOP:\n{sop}\n\n"
        f"Platform Knowledge:\n{knowledge}\n\n"
        f"Past Campaign Context:\n{state.get('episodic_context', 'None')}"
    )

    response = _llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])

    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}

    campaign_plan: CampaignPlan = {
        "objective": parsed.get("objective", f"Drive {state['campaign_goal']} for {state['product_name']}"),
        "kpis": parsed.get("kpis", ["CTR > 0.5%", "CPL < $100", "10 qualified leads/week"]),
        "timeline": parsed.get("timeline", "4-week campaign"),
        "platforms": parsed.get("platforms", state["platforms"]),
        "messaging_pillars": parsed.get("messaging_pillars", ["Value", "Trust", "Action"]),
    }

    summary = parsed.get("strategy_summary", "Campaign strategy generated.")

    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "planner",
        "type": "strategy",
        "title": "Campaign Strategy Created",
        "content": (
            f"Objective: {campaign_plan['objective']}\n"
            f"KPIs: {', '.join(campaign_plan['kpis'])}\n"
            f"Timeline: {campaign_plan['timeline']}\n"
            f"Messaging Pillars: {', '.join(campaign_plan['messaging_pillars'])}"
        ),
        "memory_reads": ["procedural", "semantic", "episodic"],
        "data": campaign_plan,
    }

    return {
        "campaign_plan": campaign_plan,
        "events": state.get("events", []) + [event],
    }
