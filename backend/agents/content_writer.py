"""
Content Writer Agent — GPT-4o

Generates one ad copy variant per requested platform (driven by state["platforms"]):
  - "linkedin"  → linkedin_post  (organic, 800-1500 chars, hashtags)
  - "twitter"   → twitter_post   (punchy, ≤280 chars, emoji)

Each variant follows the AIDA framework and messaging pillars from the campaign plan.
On revision loops, incorporates critic feedback.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AdVariant, CampaignState
from memory.semantic import retrieve_knowledge
from memory.procedural import retrieve_procedures

_llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# Map UI platform name → (variant type, per-platform copy rules)
_PLATFORM_SPECS: dict[str, dict] = {
    "linkedin": {
        "variant_type": "linkedin_post",
        "rules": (
            "linkedin_post: 800-1,500 chars total. "
            "Hook in the first line (visible before 'see more'). "
            "3-5 relevant hashtags at the end. End with a question to drive comments. "
            "Use line breaks for readability."
        ),
    },
    "twitter": {
        "variant_type": "twitter_post",
        "rules": (
            "twitter_post: HARD limit 260 chars (leave room for hashtags). "
            "One punchy insight or hook. 1-2 relevant hashtags. Include an emoji. "
            "No filler — every word must earn its place."
        ),
    },
}

_SYSTEM_BASE = """You are an expert B2B copywriter specialising in social media advertising.
Write compelling ad copy that drives real business outcomes.

IMPORTANT: Respond ONLY with a valid JSON array of ad variant objects. No markdown, no explanation.

Each object must have:
  "platform": string  — exact platform key provided in the instructions
  "headline": string  — attention-grabbing opening line
  "body":     string  — main copy body
  "cta":      string  — call to action
  "image_prompt": string | null

General rules:
- Use AIDA (Attention, Interest, Desire, Action)
- Incorporate the messaging pillars naturally
- No generic phrases like "game-changer", "revolutionary", or "unlock"
- Be specific: use numbers, outcomes, and concrete benefits
"""


def content_writer_node(state: CampaignState) -> dict:
    """LangGraph node: generates one ad copy variant per requested platform."""

    plan = state.get("campaign_plan") or {}
    findings = state.get("research_findings", "")
    revision_count = state.get("revision_count", 0)

    # Resolve which platforms the user actually selected → variant specs
    requested = [p.lower() for p in state.get("platforms", ["linkedin", "twitter"])]
    active_specs = [
        spec for key, spec in _PLATFORM_SPECS.items() if key in requested
    ]
    # Fallback: if no known platform matched, default to both
    if not active_specs:
        active_specs = list(_PLATFORM_SPECS.values())

    platform_rules = "\n".join(f"- {s['rules']}" for s in active_specs)
    expected_variants = "\n".join(
        f'  {{"platform": "{s["variant_type"]}", "headline": "...", "body": "...", "cta": "...", "image_prompt": null}}'
        for s in active_specs
    )
    system_prompt = (
        f"{_SYSTEM_BASE}\n"
        f"Generate EXACTLY {len(active_specs)} variant(s) — one per platform:\n"
        f"[\n{expected_variants}\n]\n\n"
        f"Platform-specific rules:\n{platform_rules}"
    )

    # Guard: critic_score can only exist after the first critic pass, which
    # only happens after revision_count >= 1. The `revision_count > 0` check
    # is therefore load-bearing — removing it would surface feedback text on
    # the very first generation where no score exists yet.
    critic_feedback = ""
    if revision_count > 0 and state.get("critic_score"):
        critic_feedback = (
            f"\n\nPREVIOUS CRITIC FEEDBACK (revision {revision_count}):\n"
            f"{state['critic_score'].get('feedback', '')}\n"
            f"Previous score: {state['critic_score'].get('overall', 0):.2f}\n"
            f"Please address ALL feedback points."
        )

    knowledge = retrieve_knowledge(f"ad copywriting {state['campaign_goal']} {' '.join(requested)}")
    sop = retrieve_procedures("ad content creation copywriting")

    prompt = (
        f"Product: {state['product_name']}\n"
        f"Description: {state['product_description']}\n"
        f"Campaign Goal: {state['campaign_goal']}\n"
        f"Target Audience: {state['target_audience']}\n"
        f"Tone: {state['tone']}\n"
        f"Messaging Pillars: {', '.join(plan.get('messaging_pillars', ['Value', 'Trust', 'Action']))}\n"
        f"Campaign Objective: {plan.get('objective', '')}\n\n"
        f"Research Insights:\n{findings[:2000]}\n\n"
        f"Copywriting Knowledge:\n{knowledge[:800]}\n\n"
        f"SOPs:\n{sop[:600]}"
        f"{critic_feedback}"
    )

    response = _llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])

    try:
        raw_variants = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", response.content, re.DOTALL)
        raw_variants = json.loads(match.group()) if match else []

    # Align parsed variants to expected platforms — guarantees correct count and order
    final_variants: list[AdVariant] = []
    for i, spec in enumerate(active_specs):
        v = raw_variants[i] if i < len(raw_variants) else {}
        final_variants.append({
            "platform": spec["variant_type"],
            "headline": v.get("headline", ""),
            "body": v.get("body", ""),
            "cta": v.get("cta", "Learn More"),
            "image_prompt": v.get("image_prompt"),
        })

    action = "Generated" if revision_count == 0 else f"Revised (attempt {revision_count + 1})"
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "content_writer",
        "type": "content",
        "title": f"{action} Ad Copy — {', '.join(s['variant_type'] for s in active_specs)}",
        "content": (
            f"Created {len(final_variants)} variant(s) for: "
            f"{', '.join(v['platform'] for v in final_variants)}"
        ),
        "memory_reads": ["semantic", "procedural"],
        "data": final_variants,
        "revision": revision_count,
    }

    return {
        "ad_variants": final_variants,
        "events": state.get("events", []) + [event],
    }
