# Agent Responsibilities and Flow

- **Orchestrator / Coordinator**: entry point; parses the brief, loads memory context, and routes execution across agents.
- **Campaign Strategist (Planner)**: defines objective, KPIs, messaging pillars, and campaign plan.
- **Researcher**: gathers external insights (market, competitors, audience, platform context) using search tools.
- **Content Writer**: generates platform-specific post/ad variants from strategy + research.
- **Targeting Agent**: builds audience segments (seniority, industry, geo, interests) for distribution fit.
- **Critic Agent**: scores quality/compliance/brand alignment; if score is low, sends feedback for rewrite. 
- **Publisher**: publishes approved content to LinkedIn/Buffer and records publish outputs.

## Agent Links / Flow

`User Brief -> Orchestrator -> Strategist -> Researcher -> Content Writer -> Targeting -> Critic -> (if score < 0.8 -> Content Writer loop) -> Publisher -> UI updates via SSE`

## Critic Scoring (Implementation)

- Critic agent sends campaign context + all ad variants to `gpt-4o`.
- Prompt asks model to score these dimensions `0.0–1.0`:
  - `engagement_potential`
  - `brand_alignment`
  - `platform_compliance`
  - `message_clarity`
  - `audience_resonance`
- Model returns JSON with:
  - `overall`
