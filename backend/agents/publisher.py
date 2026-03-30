"""
Publisher Agent — Buffer (LinkedIn + X/Twitter)

Publishes the approved campaign content:
  1. LinkedIn variants  → posted to "Autonomous Campaign Agent" LinkedIn page via Buffer
  2. Twitter variants   → posted to @siddarth1289300 on X via Buffer (auto-trimmed to 280 chars)
  3. Saves the completed campaign as Episodic Memory.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from graph.state import CampaignState, PublishResult
from memory.memory_manager import memory_manager
from tools.buffer_tool import schedule_via_buffer


# Maps variant type → Buffer platform target(s)
_VARIANT_PLATFORM_MAP = {
    "linkedin_post": "linkedin",
    "twitter_post":  "twitter",
}


def _build_post_text(variant: dict) -> str:
    """Compose post text from a variant dict."""
    parts = []
    if variant.get("headline"):
        parts.append(variant["headline"])
    if variant.get("body"):
        parts.append(variant["body"])
    if variant.get("cta"):
        parts.append(f"→ {variant['cta']}")
    return "\n\n".join(filter(None, parts))


def publisher_node(state: CampaignState) -> dict:
    """LangGraph node: schedules all variants via Buffer (LinkedIn + X) and saves episodic memory."""

    variants = state.get("ad_variants", [])
    publish_mode = state.get("publish_mode", "now")        # "now" | "scheduled" | "both"
    schedule_cadence = state.get("schedule_cadence", "daily_1")
    errors: list[str] = []
    buffer_update_ids: list[str] = []
    linkedin_ids: list[str] = []
    twitter_ids: list[str] = []

    # Map cadence → hours between each post slot
    _CADENCE_HOURS = {
        "daily_1": 24,
        "daily_2": 12,
        "weekly":  168,
        "custom":  24,   # default spacing for custom; description is stored for reference
    }
    interval_hours = _CADENCE_HOURS.get(schedule_cadence, 24)

    for i, variant in enumerate(variants):
        scheduled_at = (
            datetime.now(timezone.utc) + timedelta(hours=interval_hours * (i + 1))
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        text = _build_post_text(variant)
        if not text.strip():
            continue

        # Resolve post_now and scheduled_at per publish_mode
        if publish_mode == "now":
            post_now = True
            send_scheduled_at = None
        elif publish_mode == "scheduled":
            post_now = False
            send_scheduled_at = scheduled_at
        else:  # "both" — first variant live now, rest scheduled
            post_now = (i == 0)
            send_scheduled_at = None if i == 0 else scheduled_at

        # Determine which platforms to post to based on variant type
        platform_key = variant.get("platform", "buffer")
        platforms = _VARIANT_PLATFORM_MAP.get(platform_key, "linkedin,twitter")

        result = schedule_via_buffer(
            text=text,
            scheduled_at=send_scheduled_at,
            platforms=platforms,
            post_now=post_now,
        )

        if result.get("success"):
            for update in result.get("updates", []):
                uid = update.get("update_id")
                if uid:
                    buffer_update_ids.append(uid)
                    if update.get("platform") == "linkedin":
                        linkedin_ids.append(uid)
                    elif update.get("platform") == "twitter":
                        twitter_ids.append(uid)
                if update.get("error"):
                    errors.append(
                        f"Buffer ({update.get('platform','?')}) variant {i+1}: {update['error']}"
                    )
        else:
            errors.append(
                f"Buffer schedule failed (variant {i+1} / {platform_key}): "
                f"{result.get('error', 'unknown')}"
            )

    publish_result: PublishResult = {
        "buffer_update_ids": buffer_update_ids,
        "linkedin_ids": linkedin_ids,
        "twitter_ids": twitter_ids,
        "published_at": datetime.utcnow().isoformat(),
        "errors": errors,
    }

    # ── Save to Episodic Memory ───────────────────────────────────────────
    memory_manager.save_episode(
        session_id=state["session_id"],
        product_name=state["product_name"],
        campaign_goal=state["campaign_goal"],
        target_audience=state["target_audience"],
        campaign_plan=state.get("campaign_plan"),
        ad_variants=variants,
        critic_score=state.get("critic_score"),
        publish_result=publish_result,
    )

    success = len(buffer_update_ids) > 0
    status = "published" if success else "failed"

    # ── Build summary for the live event feed ────────────────────────────
    summary_lines = []
    mode_label = {"now": "published now", "scheduled": "scheduled", "both": "published + scheduled"}.get(publish_mode, "published")
    if linkedin_ids:
        summary_lines.append(
            f"✓ {len(linkedin_ids)} post(s) {mode_label} → LinkedIn (Autonomous Campaign Agent)"
        )
    if twitter_ids:
        summary_lines.append(
            f"✓ {len(twitter_ids)} post(s) {mode_label} → X/Twitter (@siddarth1289300)"
        )
    for e in errors:
        summary_lines.append(f"✗ {e}")
    summary_lines.append("✓ Campaign saved to Episodic Memory")

    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "publisher",
        "type": "publish",
        "title": f"Campaign {'Live on LinkedIn + X' if success else 'Failed'}",
        "content": "\n".join(summary_lines),
        "memory_writes": ["episodic"],
        "data": publish_result,
    }

    return {
        "publish_result": publish_result,
        "status": status,
        "events": state.get("events", []) + [event],
    }
