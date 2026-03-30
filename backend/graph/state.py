"""
CampaignState — the single source of truth passed between every LangGraph node.
Working Memory lives here: all in-flight data is stored and mutated on this dict.
"""
from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class AdVariant(TypedDict):
    platform: str          # "linkedin_post" | "linkedin_ad" | "buffer"
    headline: str
    body: str
    cta: str
    image_prompt: Optional[str]


class AudienceSegment(TypedDict):
    segment_name: str
    seniority: list[str]
    industries: list[str]
    geo: list[str]
    interests: list[str]


class CriticScore(TypedDict):
    overall: float         # 0.0 – 1.0
    engagement: float
    brand_alignment: float
    platform_compliance: float
    feedback: str          # free-text suggestions


class CampaignPlan(TypedDict):
    objective: str
    kpis: list[str]
    timeline: str
    platforms: list[str]
    messaging_pillars: list[str]


class PublishResult(TypedDict):
    buffer_update_ids: list[str]   # Buffer post IDs (LinkedIn + X/Twitter)
    linkedin_ids: list[str]        # subset posted to LinkedIn channel
    twitter_ids: list[str]         # subset posted to X/Twitter channel
    published_at: Optional[str]
    errors: list[str]


class CampaignState(TypedDict):
    # ── User input ────────────────────────────────────────────────
    session_id: str
    product_name: str
    product_description: str
    product_url: Optional[str]  # landing page URL for targeted research
    usp: str                    # unique selling proposition — sharper hook anchor
    cta_goal: str               # specific CTA e.g. "Book a Demo", "Start Free Trial"
    cta_link: str               # URL the CTA links to — embedded in copy
    campaign_goal: str          # e.g. "brand awareness", "lead generation"
    target_audience: str        # free-text from user
    tone: str                   # e.g. "professional", "casual", "bold"
    platforms: list[str]        # ["linkedin", "twitter"]
    publish_mode: str           # "now" | "scheduled" | "both"
    schedule_cadence: str       # "daily_1" | "daily_2" | "weekly" | "custom"
    custom_cadence: str         # free-text description when cadence="custom"

    # ── Conversation history (persisted to SQLite) ────────────────
    messages: list[dict[str, str]]   # {"role": "user"|"assistant", "content": "..."}

    # ── Coordinator outputs ───────────────────────────────────────
    task_plan: list[str]             # ordered steps decided by coordinator
    coordinator_notes: str

    # ── Memory context injected at runtime ───────────────────────
    episodic_context: str            # similar past campaigns (raw)
    campaign_lessons: dict[str, Any] # distilled lessons: best tones, pillars, CTAs
    semantic_context: str            # platform/ad knowledge
    procedural_context: str          # SOPs loaded for current step
    conversation_context: str        # rolling summary + recent message tail
    entities: dict[str, Any]         # extracted entities (brand, persona, etc.)

    # ── Agent outputs (working memory slots) ─────────────────────
    campaign_plan: Optional[CampaignPlan]
    research_findings: str
    ad_variants: list[AdVariant]
    audience_segments: list[AudienceSegment]
    critic_score: Optional[CriticScore]

    # ── Control flow ──────────────────────────────────────────────
    revision_count: int              # how many critic loops have run
    max_revisions: int               # default 3

    # ── Final output ──────────────────────────────────────────────
    publish_result: Optional[PublishResult]
    status: str                      # "running" | "published" | "failed"
    error: Optional[str]

    # ── SSE event log (streamed to frontend) ─────────────────────
    events: list[dict[str, Any]]
