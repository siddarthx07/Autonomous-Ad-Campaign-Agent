"""
Web Search Tool — Tavily API wrapper.

Used by the Research Agent to fetch real-time information about:
  - Competitor campaigns and messaging
  - Industry trends and news
  - Target audience pain points
  - Platform ad format updates
"""
from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import tool
from tavily import TavilyClient


def _get_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY not set")
    return TavilyClient(api_key=api_key)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for up-to-date information.
    Returns a formatted string of search results with titles, URLs, and snippets.

    Args:
        query: The search query string.
        max_results: Number of results to return (default 5).
    """
    try:
        client = _get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )

        lines = []

        if response.get("answer"):
            lines.append(f"Summary: {response['answer']}\n")

        for i, result in enumerate(response.get("results", []), 1):
            lines.append(
                f"[{i}] {result.get('title', 'No title')}\n"
                f"    URL: {result.get('url', '')}\n"
                f"    {result.get('content', '')[:400]}"
            )

        return "\n\n".join(lines) if lines else "No results found."

    except Exception as e:
        return f"Search failed: {str(e)}"


@tool
def competitive_research(product_category: str, platform: str = "LinkedIn") -> str:
    """
    Research competitor ad strategies for a given product category on a platform.

    Args:
        product_category: The product/service category to research.
        platform: The advertising platform to focus on.
    """
    queries = [
        f"best {product_category} {platform} ad campaigns 2024",
        f"{product_category} {platform} marketing strategy examples",
        f"{product_category} target audience pain points {platform}",
    ]

    results = []
    client = _get_client()

    for q in queries:
        try:
            resp = client.search(query=q, max_results=3, search_depth="basic")
            if resp.get("answer"):
                results.append(f"Q: {q}\nA: {resp['answer']}")
        except Exception:
            continue

    return "\n\n---\n\n".join(results) if results else "No competitive research found."
