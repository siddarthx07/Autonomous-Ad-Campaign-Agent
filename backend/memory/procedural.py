"""
Procedural Memory — ChromaDB collection `procedures`.

Stores Standard Operating Procedures (SOPs) for agent workflows.
Agents query this at runtime to retrieve step-by-step instructions
relevant to their current task (e.g. "how to create a LinkedIn ad").
"""
from __future__ import annotations

import os
import threading

import chromadb
from chromadb.utils import embedding_functions

_seed_lock = threading.Lock()
_seeded = False


_COLLECTION = "procedures"

_SEED_PROCEDURES = [
    {
        "id": "linkedin_ad_creation_sop",
        "text": (
            "SOP: LinkedIn Ad Creation Workflow\n"
            "1. Define campaign objective (Brand Awareness / Lead Gen / Website Traffic).\n"
            "2. Set target audience: Job Title + Seniority + Industry + Company Size.\n"
            "3. Choose ad format: Single Image, Carousel, Video, or Message Ad.\n"
            "4. Write headline (max 70 chars): lead with value proposition.\n"
            "5. Write intro text (max 150 chars): hook + social proof.\n"
            "6. Create 3 variants (A/B/C) with different headlines.\n"
            "7. Select CTA button aligned with objective.\n"
            "8. Set bid strategy: Maximum Delivery for awareness, Target CPA for leads.\n"
            "9. Set daily/lifetime budget.\n"
            "10. Activate campaign. Monitor CTR daily for first 72 hours.\n"
            "11. Pause underperforming variants (CTR < 0.3%) after 500 impressions."
        ),
    },
    {
        "id": "campaign_launch_checklist",
        "text": (
            "SOP: Campaign Launch Checklist\n"
            "□ Campaign objective defined and agreed with stakeholders.\n"
            "□ Target audience segment documented (size > 50,000 for scale).\n"
            "□ UTM parameters added to all destination URLs.\n"
            "□ Conversion tracking pixel installed and verified.\n"
            "□ Ad creative reviewed for brand guidelines compliance.\n"
            "□ Legal/compliance review completed (disclaimers, regulatory requirements).\n"
            "□ Budget approved and scheduled.\n"
            "□ Reporting dashboard set up.\n"
            "□ Team notified of launch date.\n"
            "□ 24-hour monitoring schedule assigned."
        ),
    },
    {
        "id": "content_review_sop",
        "text": (
            "SOP: Ad Content Quality Review\n"
            "Evaluate each ad variant on:\n"
            "1. Clarity: Can the reader understand the offer in 3 seconds?\n"
            "2. Relevance: Does the copy speak directly to the target persona's pain?\n"
            "3. Value Proposition: Is the benefit concrete and specific?\n"
            "4. CTA Strength: Is the action clear and friction-free?\n"
            "5. Brand Voice: Does tone match brand guidelines?\n"
            "6. Platform Compliance: Within character limits? No prohibited content?\n"
            "7. Grammar/Spelling: Zero errors.\n"
            "Scoring rubric: Each criterion 0–10. Total / 70 = quality score. "
            "Threshold for publication: 0.80 (56/70)."
        ),
    },
    {
        "id": "audience_research_sop",
        "text": (
            "SOP: Audience Research Process\n"
            "1. Search for recent articles on target audience pain points (last 6 months).\n"
            "2. Review competitor ads using LinkedIn Ad Library.\n"
            "3. Identify 3–5 key audience personas (role, goal, challenge, preferred content).\n"
            "4. Map audience to buyer journey stage (awareness/consideration/decision).\n"
            "5. Identify top 3 objections the audience has to the product category.\n"
            "6. Document key industry terminology and phrases the audience uses.\n"
            "7. Find relevant LinkedIn Groups and hashtag communities for organic seeding."
        ),
    },
    {
        "id": "ab_test_sop",
        "text": (
            "SOP: A/B Testing Ad Variants\n"
            "1. Test one variable at a time (headline OR image OR CTA, not multiple).\n"
            "2. Run each variant simultaneously with equal budget allocation.\n"
            "3. Minimum sample: 500 impressions per variant before drawing conclusions.\n"
            "4. Primary metric: CTR. Secondary: CPL or conversion rate.\n"
            "5. Statistical significance threshold: 95% confidence.\n"
            "6. Pause losing variant and allocate 100% budget to winner.\n"
            "7. Document learnings in campaign notes for future reference.\n"
            "8. Start next A/B test within 2 weeks of declaring a winner."
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
    """
    Seed once per process lifetime using double-checked locking to prevent
    concurrent requests from both seeing count() == 0 and double-inserting.
    """
    global _seeded
    if _seeded or col.count() > 0:
        return
    with _seed_lock:
        if _seeded:
            return
        col.upsert(
            ids=[p["id"] for p in _SEED_PROCEDURES],
            documents=[p["text"] for p in _SEED_PROCEDURES],
            metadatas=[{"source": "seed"} for _ in _SEED_PROCEDURES],
        )
        _seeded = True


def retrieve_procedures(query: str, n_results: int = 2) -> str:
    """Retrieve relevant SOPs for a given agent task."""
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


def add_procedure(proc_id: str, text: str, metadata: dict | None = None) -> None:
    """Add a custom SOP (e.g. client-specific workflow)."""
    col = _get_collection()
    col.upsert(
        ids=[proc_id],
        documents=[text],
        metadatas=[metadata or {}],
    )
