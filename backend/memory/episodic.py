"""
Episodic Memory — ChromaDB collection `episodes`.

Stores full campaign execution snapshots after each run so future campaigns
can retrieve similar past experiences as few-shot context.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions


_COLLECTION = "episodes"


def _get_collection() -> chromadb.Collection:
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    client = chromadb.PersistentClient(path=persist_dir)
    ef = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(_COLLECTION, embedding_function=ef)


def store_episode(
    session_id: str,
    product_name: str,
    campaign_goal: str,
    target_audience: str,
    campaign_plan: dict,
    ad_variants: list[dict],
    critic_score: dict,
    publish_result: Optional[dict] = None,
) -> None:
    """Persist a completed campaign execution as an episode."""
    col = _get_collection()

    document = json.dumps(
        {
            "product_name": product_name,
            "campaign_goal": campaign_goal,
            "target_audience": target_audience,
            "campaign_plan": campaign_plan,
            "ad_variants": ad_variants,
            "critic_score": critic_score,
            "publish_result": publish_result,
            "timestamp": datetime.utcnow().isoformat(),
        },
        indent=2,
    )

    metadata = {
        "session_id": session_id,
        "product_name": product_name,
        "campaign_goal": campaign_goal,
        "timestamp": datetime.utcnow().isoformat(),
        "critic_overall": critic_score.get("overall", 0.0) if critic_score else 0.0,
    }

    col.upsert(
        ids=[session_id],
        documents=[document],
        metadatas=[metadata],
    )


def retrieve_similar_episodes(
    query: str,
    n_results: int = 3,
) -> str:
    """Return a formatted string of the most similar past campaigns."""
    col = _get_collection()

    try:
        results = col.query(
            query_texts=[query],
            n_results=min(n_results, col.count()),
        )
    except Exception:
        return "No past campaigns found."

    if not results["documents"] or not results["documents"][0]:
        return "No past campaigns found."

    episodes = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        episodes.append(
            f"--- Past Campaign ({meta.get('timestamp', 'unknown')}) ---\n{doc}"
        )

    return "\n\n".join(episodes)


def extract_campaign_lessons(
    query: str,
    n_results: int = 5,
) -> dict:
    """
    Distil actionable lessons from past similar campaigns.

    Returns a structured dict with:
      - best_tones: tones that appeared in high-scoring (≥0.7) campaigns
      - avoid_tones: tones that only appeared in low-scoring (<0.5) campaigns
      - top_pillars: messaging pillars from best-performing campaigns
      - best_ctas: CTAs that appeared in top variants
      - top_score: best critic overall score seen for similar campaigns
      - lesson_summary: human-readable bullet list for prompt injection
    """
    col = _get_collection()
    count = col.count()
    if count == 0:
        return {"lesson_summary": "No past campaigns to learn from yet.", "top_score": 0}

    try:
        results = col.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )
    except Exception:
        return {"lesson_summary": "Could not load past campaigns.", "top_score": 0}

    if not results["documents"] or not results["documents"][0]:
        return {"lesson_summary": "No similar past campaigns found.", "top_score": 0}

    tone_scores: dict[str, list[float]] = {}
    pillar_scores: dict[str, list[float]] = {}
    cta_scores: dict[str, list[float]] = {}
    top_score = 0.0
    best_episode_summary = ""

    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        try:
            ep = json.loads(doc)
        except (json.JSONDecodeError, TypeError):
            continue

        score: float = float(
            meta.get("critic_overall")
            or (ep.get("critic_score") or {}).get("overall", 0)
            or 0
        )

        # Tone from the episode (stored inside campaign_plan or directly in episode)
        tone = (ep.get("campaign_plan") or {}).get("tone") or ""

        # Messaging pillars
        pillars: list[str] = (ep.get("campaign_plan") or {}).get("messaging_pillars", [])

        # CTAs from ad variants
        variants: list[dict] = ep.get("ad_variants") or []
        ctas = [v.get("cta", "") for v in variants if v.get("cta")]

        if tone:
            tone_scores.setdefault(tone, []).append(score)

        for pillar in pillars:
            if pillar:
                pillar_scores.setdefault(pillar, []).append(score)

        for cta in ctas:
            if cta:
                cta_scores.setdefault(cta, []).append(score)

        if score > top_score:
            top_score = score
            goal = ep.get("campaign_goal", "")
            product = ep.get("product_name", "")
            best_episode_summary = (
                f"{product} / {goal} — critic score {score:.2f}"
            )

    def _avg(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    # Rank tones
    tone_avgs = {t: _avg(s) for t, s in tone_scores.items()}
    best_tones = [t for t, s in sorted(tone_avgs.items(), key=lambda x: -x[1]) if s >= 0.65]
    avoid_tones = [t for t, s in tone_avgs.items() if s < 0.45 and t not in best_tones]

    # Top pillars (appear in ≥0.65 avg score episodes)
    pillar_avgs = {p: _avg(s) for p, s in pillar_scores.items()}
    top_pillars = [p for p, s in sorted(pillar_avgs.items(), key=lambda x: -x[1])[:4] if s >= 0.6]

    # Best CTAs
    cta_avgs = {c: _avg(s) for c, s in cta_scores.items()}
    best_ctas = [c for c, s in sorted(cta_avgs.items(), key=lambda x: -x[1])[:3] if s >= 0.6]

    # Build human-readable lesson bullets
    bullets: list[str] = []
    if best_episode_summary:
        bullets.append(f"Best past run: {best_episode_summary}")
    if best_tones:
        bullets.append(f"Tones that scored well: {', '.join(best_tones)}")
    if avoid_tones:
        bullets.append(f"Tones to avoid (low scores): {', '.join(avoid_tones)}")
    if top_pillars:
        bullets.append(f"High-performing messaging pillars: {', '.join(top_pillars)}")
    if best_ctas:
        bullets.append(f"CTAs from top campaigns: {', '.join(best_ctas)}")
    if not bullets:
        bullets.append("Not enough scored data yet to extract lessons.")

    return {
        "best_tones": best_tones,
        "avoid_tones": avoid_tones,
        "top_pillars": top_pillars,
        "best_ctas": best_ctas,
        "top_score": round(top_score, 2),
        "lesson_summary": "\n".join(f"• {b}" for b in bullets),
    }
