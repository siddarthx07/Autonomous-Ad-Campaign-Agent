"""
Publisher Agent — LinkedIn API + Buffer API

Publishes the approved campaign content:
  1. Posts the best-scoring variant as a LinkedIn organic post.
  2. Schedules remaining variants via Buffer for future distribution.
  3. Saves the completed campaign as Episodic Memory for future reference.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from graph.state import CampaignState, PublishResult
from memory.memory_manager import memory_manager
from tools.linkedin_tool import post_to_linkedin
from tools.buffer_tool import schedule_via_buffer


def _build_linkedin_text(variant: dict, campaign: dict) -> str:
    """Compose full LinkedIn post text from a variant."""
    parts = []

    if variant.get("headline"):
        parts.append(variant["headline"])

    if variant.get("body"):
        parts.append("")
        parts.append(variant["body"])

    if variant.get("cta"):
        parts.append("")
        parts.append(f"👉 {variant['cta']}")

    return "\n".join(parts)


def _build_buffer_text(variant: dict) -> str:
    """Compose Buffer post text from a variant."""
    parts = []

    if variant.get("headline"):
        parts.append(variant["headline"])

    if variant.get("body"):
        parts.append(variant["body"])

    if variant.get("cta"):
        parts.append(f"→ {variant['cta']}")

    return "\n\n".join(filter(None, parts))


def publisher_node(state: CampaignState) -> dict:
    """LangGraph node: publishes approved content and saves episodic memory."""

    variants = state.get("ad_variants", [])
    plan = state.get("campaign_plan") or {}
    errors = []
    linkedin_post_id = None
    linkedin_ad_id = None
    buffer_update_ids = []

    # Find the LinkedIn post variant
    linkedin_variant = next(
        (v for v in variants if v["platform"] == "linkedin_post"), None
    )
    linkedin_ad_variant = next(
        (v for v in variants if v["platform"] == "linkedin_ad"), None
    )
    buffer_variant = next(
        (v for v in variants if v["platform"] == "buffer"), None
    )

    # ── Publish to LinkedIn ───────────────────────────────────────
    if linkedin_variant:
        text = _build_linkedin_text(linkedin_variant, plan)
        result = post_to_linkedin(text=text, visibility="PUBLIC")

        if result.get("success"):
            linkedin_post_id = result.get("post_id")
        else:
            errors.append(f"LinkedIn post failed: {result.get('error', 'unknown')}")

    # ── Schedule via Buffer ───────────────────────────────────────
    buffer_variants_to_schedule = [v for v in [linkedin_ad_variant, buffer_variant] if v]

    # Stagger scheduling: now + 1 day, now + 2 days
    for i, bv in enumerate(buffer_variants_to_schedule):
        scheduled_at = (
            datetime.now(timezone.utc) + timedelta(days=i + 1)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        text = _build_buffer_text(bv)
        result = schedule_via_buffer(text=text, scheduled_at=scheduled_at)

        if result.get("success"):
            for update in result.get("updates", []):
                if update.get("update_id"):
                    buffer_update_ids.append(update["update_id"])
        else:
            errors.append(f"Buffer schedule failed: {result.get('error', 'unknown')}")

    # ── Save to Episodic Memory ───────────────────────────────────
    memory_manager.save_episode(
        session_id=state["session_id"],
        product_name=state["product_name"],
        campaign_goal=state["campaign_goal"],
        target_audience=state["target_audience"],
        campaign_plan=state.get("campaign_plan"),
        ad_variants=variants,
        critic_score=state.get("critic_score"),
        publish_result={
            "linkedin_post_id": linkedin_post_id,
            "buffer_update_ids": buffer_update_ids,
            "errors": errors,
        },
    )

    publish_result: PublishResult = {
        "linkedin_post_id": linkedin_post_id,
        "linkedin_ad_id": linkedin_ad_id,
        "buffer_update_ids": buffer_update_ids,
        "published_at": datetime.utcnow().isoformat(),
        "errors": errors,
    }

    success = linkedin_post_id is not None or len(buffer_update_ids) > 0
    status = "published" if success else ("partial" if not errors else "failed")

    summary_lines = []
    if linkedin_post_id:
        summary_lines.append(f"✓ LinkedIn post published (ID: {linkedin_post_id})")
    if buffer_update_ids:
        summary_lines.append(f"✓ {len(buffer_update_ids)} posts scheduled via Buffer")
    for e in errors:
        summary_lines.append(f"✗ {e}")
    summary_lines.append("✓ Campaign saved to Episodic Memory")

    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "publisher",
        "type": "publish",
        "title": f"Campaign {'Published' if success else 'Partially Published'}",
        "content": "\n".join(summary_lines),
        "memory_writes": ["episodic"],
        "data": publish_result,
    }

    return {
        "publish_result": publish_result,
        "status": status,
        "events": state.get("events", []) + [event],
    }
