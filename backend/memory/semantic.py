"""
Semantic Memory — ChromaDB collection `knowledge`.

Pre-seeded with LinkedIn/Buffer ad specs, copywriting rules, and platform best
practices. Queried during planning and content writing to ground agent reasoning.
"""
from __future__ import annotations

import os

import chromadb
from chromadb.utils import embedding_functions


_COLLECTION = "knowledge"

_SEED_DOCUMENTS = [
    {
        "id": "linkedin_post_spec",
        "text": (
            "LinkedIn Post Best Practices: "
            "Posts perform best at 1,300–2,000 characters. Lead with a hook in the first line "
            "(visible before 'see more'). Use 3–5 relevant hashtags at the end. "
            "Native documents and carousels get 3x more reach than external links. "
            "Best posting times: Tuesday–Thursday 8–10am or 12pm. "
            "Emojis increase engagement by ~50% when used sparingly. "
            "Always end with a question to drive comments."
        ),
    },
    {
        "id": "linkedin_ad_spec",
        "text": (
            "LinkedIn Ad Specifications: "
            "Single Image Ad: Headline max 70 chars, Intro text max 150 chars, "
            "Image size 1200x627px. "
            "Sponsored Content: Max 3 lines of body text before truncation on mobile. "
            "Message Ads: Subject max 60 chars, body max 1,500 chars. "
            "CTA options: Apply Now, Download, Get Quote, Learn More, Register, Sign Up, Subscribe, View Quote. "
            "LinkedIn ads CPM averages $6–$9. CTR benchmark: 0.44%–0.65%. "
            "B2B audiences respond best to ROI-driven messaging, data points, and case studies."
        ),
    },
    {
        "id": "buffer_scheduling",
        "text": (
            "Buffer Scheduling Best Practices: "
            "Schedule LinkedIn posts during peak hours: 7–8am, 12pm, 5–6pm on weekdays. "
            "Buffer allows up to 2,000 scheduled posts. "
            "Use Buffer's 'Best Time to Post' feature per profile. "
            "Consistent posting cadence (3–5x/week on LinkedIn) builds algorithmic preference. "
            "Mix content types: 40% educational, 30% promotional, 20% personal/story, 10% curated."
        ),
    },
    {
        "id": "copywriting_rules",
        "text": (
            "Ad Copywriting Framework (AIDA): "
            "Attention: Grab with a bold stat, provocative question, or contrarian statement. "
            "Interest: Explain the pain point or opportunity in 1–2 sentences. "
            "Desire: Describe the transformation/outcome the product enables. "
            "Action: Clear, specific CTA with urgency. "
            "Use active voice. Avoid jargon. Short sentences (avg 15 words). "
            "Specificity converts: '3x more leads' beats 'more leads'. "
            "Social proof (numbers, names, logos) dramatically increases trust."
        ),
    },
    {
        "id": "b2b_audience_targeting",
        "text": (
            "B2B LinkedIn Audience Targeting: "
            "Layer 3+ targeting criteria to narrow CPL. "
            "Job Title targeting: combine seniority (Senior, Director, VP, C-Suite) with function. "
            "Company size: SMB (<200 employees) vs Mid-market (200–1000) vs Enterprise (1000+). "
            "Industry verticals: SaaS, FinTech, Healthcare, Manufacturing each have different buying cycles. "
            "Matched Audiences (retargeting) reduces CPL by 35%. "
            "Lookalike audiences expand reach while maintaining relevance. "
            "Exclude current customers to avoid wasted spend."
        ),
    },
    {
        "id": "campaign_objectives",
        "text": (
            "Campaign Objective Selection: "
            "Brand Awareness: optimize for impressions, use broad audiences. "
            "Lead Generation: LinkedIn Lead Gen Forms convert 3x better than landing pages on mobile. "
            "Website Traffic: use UTM parameters for attribution. "
            "Engagement: boosts organic algorithmic reach. "
            "Video Views: LinkedIn native video auto-plays at 60% watch rate. "
            "Match objective to funnel stage: awareness → engagement → conversion."
        ),
    },
    {
        "id": "performance_benchmarks",
        "text": (
            "LinkedIn Campaign Performance Benchmarks (2024): "
            "CTR: 0.44% (good), 0.65%+ (excellent). "
            "CPL (Lead Gen Forms): $50–$150 B2B average. "
            "Engagement rate: 1–5% for sponsored content. "
            "Conversion rate from LinkedIn ad: 6–10% B2B average. "
            "Frequency cap: 4 impressions/member/48hrs to avoid ad fatigue. "
            "A/B test creative every 4 weeks. Refresh copy every 6 weeks."
        ),
    },
]


def _get_collection() -> chromadb.Collection:
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    client = chromadb.PersistentClient(path=persist_dir)
    ef = embedding_functions.DefaultEmbeddingFunction()
    col = client.get_or_create_collection(_COLLECTION, embedding_function=ef)
    _seed_if_empty(col)
    return col


def _seed_if_empty(col: chromadb.Collection) -> None:
    if col.count() > 0:
        return
    col.upsert(
        ids=[d["id"] for d in _SEED_DOCUMENTS],
        documents=[d["text"] for d in _SEED_DOCUMENTS],
        metadatas=[{"source": "seed"} for _ in _SEED_DOCUMENTS],
    )


def retrieve_knowledge(query: str, n_results: int = 3) -> str:
    """Retrieve relevant platform knowledge for a given query."""
    col = _get_collection()

    try:
        results = col.query(
            query_texts=[query],
            n_results=min(n_results, col.count()),
        )
    except Exception:
        return ""

    if not results["documents"] or not results["documents"][0]:
        return ""

    return "\n\n".join(results["documents"][0])


def add_knowledge(doc_id: str, text: str, metadata: dict | None = None) -> None:
    """Add a new knowledge document (e.g. user-uploaded brand guidelines)."""
    col = _get_collection()
    col.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[metadata or {}],
    )
