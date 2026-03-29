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
