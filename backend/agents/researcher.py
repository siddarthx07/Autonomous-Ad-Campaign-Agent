"""
Research Agent — GPT-4o-mini + Tavily

Runs parallel web searches to gather:
  - Competitor ad examples and messaging
  - Industry trends and pain points
  - Target audience language and vocabulary
  - Platform-specific recent best practices

Stores research findings in working memory (state).
"""
from __future__ import annotations

import concurrent.futures
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import CampaignState
from tools.web_search import web_search, competitive_research

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Timeout for each individual Tavily search call (seconds)
_SEARCH_TIMEOUT = 12.0
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _safe_search(tool, kwargs: dict, timeout: float = _SEARCH_TIMEOUT) -> str:
    """
    Run a LangChain tool in a thread with a wall-clock timeout.
    Returns an empty string on timeout or any error so the agent
    can continue with partial results rather than hanging indefinitely.
    """
    future = _EXECUTOR.submit(tool.invoke, kwargs)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        future.cancel()
        return f"[Search timed out after {timeout}s — skipped]"
    except Exception as exc:
        return f"[Search error: {exc}]"

_SYSTEM = """You are a market research analyst specialising in digital advertising.
Your task is to synthesise web research into actionable insights for a campaign.

Using the research results provided, write a structured findings report with:
1. COMPETITOR LANDSCAPE: Key competitor messaging and positioning (2-3 bullet points)
2. AUDIENCE INSIGHTS: Pain points, language, and motivations of the target audience (3-4 bullet points)
3. TRENDING TOPICS: Relevant industry trends to leverage (2-3 bullet points)
4. MESSAGING OPPORTUNITIES: Gaps or angles competitors are missing (2-3 bullet points)
5. RECOMMENDED HOOKS: 3 strong opening hooks based on the research

Keep each section concise and directly actionable for the content writer.
"""


def researcher_node(state: CampaignState) -> dict:
    """
    LangGraph node: performs web research and synthesises findings.

    This is a synchronous node. LangGraph's astream() runs sync nodes in a
    thread pool via run_in_executor, so these calls do not block the event loop.
    _safe_search adds a per-call wall-clock timeout on top of that.
    """

    product = state["product_name"]
    goal = state["campaign_goal"]
    audience = state["target_audience"]

    # Run targeted searches
    search_results = []

    queries = [
        f"{product} LinkedIn advertising campaign examples 2024",
        f"{audience} pain points challenges 2024",
        f"{goal} marketing strategy B2B best practices",
    ]

    for q in queries:
        result = _safe_search(web_search, {"query": q, "max_results": 4})
        search_results.append(f"Search: {q}\n{result}")

    # Run competitive research
    comp_result = _safe_search(competitive_research, {
        "product_category": product,
        "platform": "LinkedIn",
    })
    search_results.append(f"Competitive Research:\n{comp_result}")

    combined_research = "\n\n---\n\n".join(search_results)

    # Synthesise with LLM
    prompt = (
        f"Campaign Context:\n"
        f"Product: {product}\nGoal: {goal}\nAudience: {audience}\n\n"
        f"Raw Research Results:\n{combined_research[:6000]}"
    )

    response = _llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    findings = response.content

    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "researcher",
        "type": "research",
        "title": "Market Research Complete",
        "content": findings[:800] + ("..." if len(findings) > 800 else ""),
        "memory_reads": [],
        "tools_used": ["tavily_web_search", "competitive_research"],
        "searches_run": len(queries) + 1,
    }

    return {
        "research_findings": findings,
        "events": state.get("events", []) + [event],
    }
