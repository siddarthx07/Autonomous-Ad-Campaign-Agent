"""
Content Writer Agent — GPT-4o

Generates 3 ad copy variants per platform:
  - LinkedIn organic post
  - LinkedIn sponsored ad (headline + intro + CTA)
  - Buffer-scheduled content post

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

_SYSTEM = """You are an expert B2B copywriter specialising in LinkedIn and social media advertising.
Write compelling ad copy that drives real business outcomes.

IMPORTANT: Respond ONLY with a valid JSON array of ad variant objects. No markdown, no explanation.

Format:
[
  {{
    "platform": "linkedin_post",
    "headline": "...",
    "body": "...",
    "cta": "...",
    "image_prompt": "..."
  }},
  {{
    "platform": "linkedin_ad",
    "headline": "...",  // max 70 chars
    "body": "...",      // max 150 chars intro text
    "cta": "Learn More",
    "image_prompt": "..."
  }},
  {{
    "platform": "buffer",
    "headline": "...",
    "body": "...",
    "cta": "...",
    "image_prompt": null
  }}
]

Rules:
- LinkedIn post: 800-1,500 chars, hook first line, 3-5 hashtags at end, end with question
- LinkedIn ad headline: max 70 chars, value-driven, specific
- LinkedIn ad body: max 150 chars intro, one key benefit + social proof
- Buffer post: punchy, engagement-focused, include emoji, max 500 chars
- All variants: use AIDA (Attention, Interest, Desire, Action)
- Incorporate messaging pillars naturally
- No generic phrases like "game-changer" or "revolutionary"
"""


def content_writer_node(state: CampaignState) -> dict:
    """LangGraph node: generates 3 ad copy variants per platform."""

    plan = state.get("campaign_plan") or {}
    findings = state.get("research_findings", "")
    critic_feedback = ""
    revision_count = state.get("revision_count", 0)

    if revision_count > 0 and state.get("critic_score"):
        critic_feedback = (
            f"\n\nPREVIOUS CRITIC FEEDBACK (revision {revision_count}):\n"
            f"{state['critic_score'].get('feedback', '')}\n"
            f"Previous score: {state['critic_score'].get('overall', 0):.2f}\n"
            f"Please address ALL feedback points."
        )

    knowledge = retrieve_knowledge(f"LinkedIn ad copywriting {state['campaign_goal']}")
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

    response = _llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])

    try:
        variants = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", response.content, re.DOTALL)
        variants = json.loads(match.group()) if match else []

    # Ensure we always have 3 variants
    platforms = ["linkedin_post", "linkedin_ad", "buffer"]
    final_variants: list[AdVariant] = []
    for i, platform in enumerate(platforms):
        if i < len(variants):
            v = variants[i]
        else:
            v = {"platform": platform, "headline": "", "body": "", "cta": "Learn More", "image_prompt": None}

        final_variants.append({
            "platform": v.get("platform", platform),
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
        "title": f"{action} Ad Copy Variants",
        "content": (
            f"Created {len(final_variants)} variants across {len(platforms)} platforms.\n"
            f"Platforms: {', '.join(v['platform'] for v in final_variants)}"
        ),
        "memory_reads": ["semantic", "procedural"],
        "data": final_variants,
        "revision": revision_count,
    }

    return {
        "ad_variants": final_variants,
        "events": state.get("events", []) + [event],
    }
