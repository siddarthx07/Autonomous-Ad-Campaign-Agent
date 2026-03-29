"""
Critic Agent — GPT-4o

Evaluates all ad variants on 5 dimensions and returns a quality score.
If overall score < 0.80, the graph loops back to the Content Writer.
If overall score >= 0.80 (or max_revisions reached), routes to Publisher.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import CriticScore, CampaignState
from memory.procedural import retrieve_procedures

_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

_SYSTEM = """You are a senior creative director and marketing critic.
Evaluate the provided ad copy variants and score the overall campaign content quality.

Score each dimension from 0.0 to 1.0:
- engagement_potential: Will this stop the scroll and drive interaction?
- brand_alignment: Does tone, messaging, and professionalism match the brand brief?
- platform_compliance: Are character limits, format rules, and CTA best practices followed?
- message_clarity: Is the value proposition immediately clear?
- audience_resonance: Will the target audience find this compelling and relevant?

Respond ONLY with valid JSON:
{{
  "overall": 0.0-1.0,
  "engagement": 0.0-1.0,
  "brand_alignment": 0.0-1.0,
  "platform_compliance": 0.0-1.0,
  "message_clarity": 0.0-1.0,
  "audience_resonance": 0.0-1.0,
  "passed": true/false,
  "feedback": "Specific, actionable feedback for the content writer. List exact issues and how to fix them. Be specific about which variant needs what change.",
  "strengths": "What's working well.",
  "top_variant": "linkedin_post|linkedin_ad|buffer"
}}

Threshold for passing: overall >= 0.80.
Be honest and demanding — mediocre content hurts campaign performance.
"""


def critic_node(state: CampaignState) -> dict:
    """LangGraph node: scores content quality and decides pass/revise."""

    variants = state.get("ad_variants", [])
    plan = state.get("campaign_plan") or {}
    sop = retrieve_procedures("ad content quality review")

    variants_text = "\n\n".join(
        f"VARIANT [{v['platform'].upper()}]\n"
        f"Headline: {v['headline']}\n"
        f"Body: {v['body']}\n"
        f"CTA: {v['cta']}"
        for v in variants
    )

    prompt = (
        f"Campaign Context:\n"
        f"Product: {state['product_name']}\n"
        f"Goal: {state['campaign_goal']}\n"
        f"Audience: {state['target_audience']}\n"
        f"Tone: {state['tone']}\n"
        f"Objective: {plan.get('objective', '')}\n"
        f"Messaging Pillars: {', '.join(plan.get('messaging_pillars', []))}\n\n"
        f"Quality Review SOP:\n{sop[:600]}\n\n"
        f"Ad Variants to Review:\n{variants_text}"
    )

    response = _llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])

    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        parsed = json.loads(match.group()) if match else {}

    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)

    overall = float(parsed.get("overall", 0.5))
    passed = parsed.get("passed", overall >= 0.80)

    # Force pass after max revisions to prevent infinite loops
    if revision_count >= max_revisions:
        passed = True

    critic_score: CriticScore = {
        "overall": overall,
        "engagement": float(parsed.get("engagement", overall)),
        "brand_alignment": float(parsed.get("brand_alignment", overall)),
        "platform_compliance": float(parsed.get("platform_compliance", overall)),
        "feedback": parsed.get("feedback", ""),
    }

    status_label = "PASSED" if passed else f"NEEDS REVISION (attempt {revision_count + 1}/{max_revisions})"
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "critic",
        "type": "critique",
        "title": f"Quality Review: {status_label}",
        "content": (
            f"Overall Score: {overall:.0%}\n"
            f"Engagement: {critic_score['engagement']:.0%} | "
            f"Brand: {critic_score['brand_alignment']:.0%} | "
            f"Compliance: {critic_score['platform_compliance']:.0%}\n\n"
            f"Strengths: {parsed.get('strengths', '')}\n\n"
            f"Feedback: {parsed.get('feedback', '')}"
        ),
        "memory_reads": ["procedural"],
        "data": {
            "scores": critic_score,
            "passed": passed,
            "top_variant": parsed.get("top_variant"),
        },
    }

    new_revision_count = revision_count + 1 if not passed else revision_count

    return {
        "critic_score": critic_score,
        "revision_count": new_revision_count,
        "events": state.get("events", []) + [event],
    }


def should_revise(state: CampaignState) -> str:
    """
    Conditional edge function: returns 'revise' or 'publish'.
    Called by LangGraph to determine routing after critic runs.
    """
    score = state.get("critic_score")
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)

    if score is None:
        return "revise"

    if score["overall"] >= 0.80 or revision_count >= max_revisions:
        return "publish"

    return "revise"
