"""
LangGraph Campaign Graph

Defines the full multi-agent pipeline as a directed state graph.

Flow:
  START
    → coordinator           (load memory, create task plan)
    → strategist            (campaign strategy)
    → researcher            (web search + synthesis)
    → content_writer        (ad copy generation)
    → targeting             (audience segments)
    → critic                (quality review)
    → [conditional edge]
        if score < 0.80 and revisions < max → content_writer (loop)
        else                                → publisher
    → publisher             (LinkedIn + Buffer + episodic store)
  END
"""
from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import StateGraph, END

from graph.state import CampaignState
from agents.coordinator import coordinator_node
from agents.strategist import strategist_node
from agents.researcher import researcher_node
from agents.content_writer import content_writer_node
from agents.targeting import targeting_node
from agents.critic import critic_node, should_revise
from agents.publisher import publisher_node


def build_graph() -> Any:
    """Compile and return the LangGraph campaign pipeline."""

    graph = StateGraph(CampaignState)

    # Register nodes
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("content_writer", content_writer_node)
    graph.add_node("targeting", targeting_node)
    graph.add_node("critic", critic_node)
    graph.add_node("publisher", publisher_node)

    # Linear edges
    graph.set_entry_point("coordinator")
    graph.add_edge("coordinator", "strategist")
    graph.add_edge("strategist", "researcher")
    graph.add_edge("researcher", "content_writer")
    graph.add_edge("content_writer", "targeting")
    graph.add_edge("targeting", "critic")

    # Conditional edge: critic decides revise vs publish
    graph.add_conditional_edges(
        "critic",
        should_revise,
        {
            "revise": "content_writer",
            "publish": "publisher",
        },
    )

    graph.add_edge("publisher", END)

    return graph.compile()


def make_initial_state(
    product_name: str,
    product_description: str,
    campaign_goal: str,
    target_audience: str,
    tone: str,
    platforms: list[str],
    product_url: str | None = None,
    usp: str = "",
    cta_goal: str = "Learn More",
    cta_link: str = "",
    publish_mode: str = "now",
    schedule_cadence: str = "daily_1",
    custom_cadence: str = "",
    session_id: str | None = None,
) -> CampaignState:
    """Create a fresh CampaignState from user inputs."""
    return CampaignState(
        session_id=session_id or str(uuid.uuid4()),
        product_name=product_name,
        product_description=product_description,
        product_url=product_url,
        usp=usp,
        cta_goal=cta_goal,
        cta_link=cta_link,
        campaign_goal=campaign_goal,
        target_audience=target_audience,
        tone=tone,
        platforms=platforms,
        publish_mode=publish_mode,
        schedule_cadence=schedule_cadence,
        custom_cadence=custom_cadence,
        messages=[],
        task_plan=[],
        coordinator_notes="",
        episodic_context="",
        campaign_lessons={},
        semantic_context="",
        procedural_context="",
        conversation_context="",
        entities={},
        campaign_plan=None,
        research_findings="",
        ad_variants=[],
        audience_segments=[],
        critic_score=None,
        revision_count=0,
        max_revisions=3,
        publish_result=None,
        status="running",
        error=None,
        events=[],
    )


# Singleton compiled graph (loaded once at import)
campaign_graph = build_graph()
