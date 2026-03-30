"""
Targeting Agent — GPT-4o-mini

Defines LinkedIn audience segments:
  - Job titles and seniority levels
  - Industries and company sizes
  - Geography
  - Interest signals and groups
  - Exclusions (competitors, existing customers)
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AudienceSegment, CampaignState
from memory.semantic import retrieve_knowledge

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

_SYSTEM = """You are a LinkedIn advertising targeting specialist.
Given a campaign brief and research, define 2-3 precise audience segments.

Respond ONLY with a valid JSON array:
[
  {{
    "segment_name": "Primary: ...",
    "seniority": ["Senior", "Director", "VP", "C-Suite"],
    "industries": ["Software & IT", "Internet"],
    "geo": ["United States", "Canada"],
    "interests": ["SaaS", "B2B Marketing"],
    "job_functions": ["Marketing", "Business Development"],
    "company_size": ["51-200", "201-500", "501-1000"],
    "estimated_reach": "50,000-80,000",
    "rationale": "one sentence explanation"
  }},
  ...
]

LinkedIn targeting options to use:
- Seniority: Entry, Associate, Senior, Manager, Director, VP, CXO, Owner, Partner
- Job Functions: Marketing, Sales, IT, Finance, Operations, Engineering, HR, etc.
- Industries: use LinkedIn's exact industry names
- Company Size: 1-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5001-10000, 10001+
"""


def targeting_node(state: CampaignState) -> dict:
    """LangGraph node: generates audience segments for LinkedIn targeting."""

    knowledge = retrieve_knowledge(
        f"LinkedIn audience targeting {state['campaign_goal']} {state['target_audience']}"
    )

    plan = state.get("campaign_plan") or {}
    findings = state.get("research_findings", "")

    prompt = (
        f"Product: {state['product_name']}\n"
        f"Campaign Goal: {state['campaign_goal']}\n"
        f"Target Audience (user-defined): {state['target_audience']}\n"
        f"Conversation Memory:\n{state.get('conversation_context', '')}\n"
        f"Campaign Objective: {plan.get('objective', '')}\n\n"
        f"Research Audience Insights:\n{findings[:1500]}\n\n"
        f"LinkedIn Targeting Knowledge:\n{knowledge[:600]}"
    )

    response = _llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])

    try:
        segments_raw = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", response.content, re.DOTALL)
        segments_raw = json.loads(match.group()) if match else []

    segments: list[AudienceSegment] = []
    for s in segments_raw:
        segments.append({
            "segment_name": s.get("segment_name", "Primary Audience"),
            "seniority": s.get("seniority", ["Senior", "Director"]),
            "industries": s.get("industries", ["Software & IT"]),
            "geo": s.get("geo", ["United States"]),
            "interests": s.get("interests", []),
        })

    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "targeting",
        "type": "targeting",
        "title": f"Audience Targeting Defined ({len(segments)} segments)",
        "content": "\n".join(
            f"• {s['segment_name']}: {', '.join(s['seniority'])} in {', '.join(s['industries'][:2])}"
            for s in segments
        ),
        "memory_reads": ["semantic"],
        "data": segments,
    }

    return {
        "audience_segments": segments,
        "events": state.get("events", []) + [event],
    }
