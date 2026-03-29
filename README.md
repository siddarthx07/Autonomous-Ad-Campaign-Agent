# Autonomous Campaign Agent

A fully autonomous multi-agent system that runs social media ad campaigns end-to-end — from brief to published post — using LangGraph, GPT-4o, and real LinkedIn + Buffer APIs.

Built as a demo for applied AI agent systems work (planning, memory, tool use, LLM orchestration).

---

## Architecture

```
User Brief
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph Campaign Graph                         │
│                                                                     │
│  Orchestrator → Planner → Researcher → Content Writer → Targeting  │
│      (GPT-4o)    (GPT-4o)  (GPT-4o-mini   (GPT-4o)    (GPT-4o-mini │
│                             + Tavily)                               │
│                                                ↓                   │
│                                             Critic                  │
│                                           (GPT-4o)                  │
│                                          ↙       ↘                  │
│                               score < 0.8    score ≥ 0.8           │
│                                  ↙                ↘                 │
│                          Content Writer         Publisher           │
│                          (loop, max 3x)   (LinkedIn + Buffer)       │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       6 Memory Systems                              │
│                                                                     │
│  Working Memory    — LangGraph CampaignState (in-flight)            │
│  Episodic Memory   — ChromaDB: past campaign runs                   │
│  Semantic Memory   — ChromaDB: platform knowledge, ad specs         │
│  Conversation Hist — SQLite: user ↔ agent messages                  │
│  Entity Memory     — SQLite: brands, personas, products             │
│  Procedural Memory — ChromaDB: SOPs, workflows                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Model | Responsibility |
|---|---|---|
| **Orchestrator** | GPT-4o | Parses brief, loads all memory, creates task plan |
| **Planning Agent** | GPT-4o | Campaign strategy, KPIs, messaging pillars |
| **Research Agent** | GPT-4o-mini | Tavily web search, competitor analysis, audience insights |
| **Content Writer** | GPT-4o | 3 ad variants per platform (AIDA framework) |
| **Targeting Agent** | GPT-4o-mini | LinkedIn audience segments, seniority, industries, geo |
| **Critic Agent** | GPT-4o | Quality review (0–1 score), loops back if < 0.80 |
| **Publisher** | — | LinkedIn post + Buffer schedule + episodic memory save |

## Memory Systems

| Type | Storage | Purpose |
|---|---|---|
| **Working** | LangGraph State | Current run data: drafts, scores, task queue |
| **Episodic** | ChromaDB | Past campaign snapshots — retrieved by similarity |
| **Semantic** | ChromaDB | LinkedIn/Buffer specs, copywriting rules — pre-seeded |
| **Conversation** | SQLite | Full message history per session |
| **Entity** | SQLite | Extracted entities: brand, product, persona, tone |
| **Procedural** | ChromaDB | SOPs: ad creation, A/B testing, launch checklist |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys (see below)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Required API Keys below)

# Start the backend
python main.py
# → Running on http://localhost:8000
```

### 2. Frontend Setup

```bash
cd frontend

# Configure environment
cp .env.local.example .env.local
# Edit if backend is on a different port

# Install and run
npm install
npm run dev
# → Running on http://localhost:3000
```

### 3. Open the App

Navigate to [http://localhost:3000](http://localhost:3000) and click **Launch New Campaign**.

---

## Required API Keys

Copy `backend/.env.example` to `backend/.env` and fill in:

### OpenAI
```
OPENAI_API_KEY=sk-...
```
Get yours at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

### Tavily (Web Search)
```
TAVILY_API_KEY=tvly-...
```
Free tier available at [app.tavily.com](https://app.tavily.com).

### LinkedIn OAuth2
```
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_PERSON_URN=urn:li:person:...
```

To get a LinkedIn access token:
1. Create an app at [linkedin.com/developers](https://www.linkedin.com/developers/apps)
2. Add `r_liteprofile` and `w_member_social` OAuth2 scopes
3. Use the OAuth2 authorization code flow to obtain a token
4. Your Person URN is `urn:li:person:{your_id}` — get your ID from `GET /v2/me`

### Buffer
```
BUFFER_ACCESS_TOKEN=...
BUFFER_PROFILE_IDS=...
```

Get your token at [buffer.com/developers/api/oauth](https://buffer.com/developers/api/oauth).
Profile IDs: call `GET /1/profiles.json` after authenticating.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/campaign/run` | Start a campaign run, returns `session_id` |
| `GET` | `/api/campaign/stream?session_id=...` | SSE stream of agent events |
| `GET` | `/api/campaign/{session_id}` | Final campaign state |
| `GET` | `/api/memory/{session_id}` | All 6 memory stores snapshot |
| `GET` | `/api/sessions` | List all campaign sessions |
| `GET` | `/api/health` | Health check |

### Example: Start a Campaign

```bash
curl -X POST http://localhost:8000/api/campaign/run \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Acme CRM",
    "product_description": "AI-powered CRM for B2B sales teams that reduces manual data entry by 80%",
    "campaign_goal": "Lead Generation",
    "target_audience": "Sales directors at B2B SaaS companies with 50-500 employees",
    "tone": "Professional",
    "budget": "$1,000/week",
    "platforms": ["linkedin", "buffer"]
  }'
```

```json
{
  "session_id": "a1b2c3d4-...",
  "message": "Campaign started. Connect to /api/campaign/stream to follow progress."
}
```

### Stream Events

```bash
curl -N http://localhost:8000/api/campaign/stream?session_id=a1b2c3d4-...
```

Each event:
```
event: agent_event
data: {"type":"agent_event","node":"planner","event":{"agent":"planner","title":"Campaign Strategy Created","content":"...","memory_reads":["procedural","semantic"]}}

event: complete
data: {"type":"complete","status":"published","publish_result":{...}}
```

---

## UI Features

1. **Dashboard** — System architecture overview + recent campaigns
2. **New Campaign form** — Campaign brief with goal, audience, tone, budget
3. **Live Agent Pipeline** — Visual graph with active node highlighting and revision counter
4. **Live Agent Feed** — Real-time SSE stream of all agent events with memory badge annotations
5. **Content Preview** — Generated ad copy variants, campaign strategy, audience segments, critic scores
6. **Memory Explorer** — Tabbed view of all 6 memory systems with live data
7. **Publish Panel** — LinkedIn post ID, Buffer schedule IDs, error reporting

---

## Project Structure

```
Multi-agent/
├── backend/
│   ├── main.py                    # FastAPI + SSE
│   ├── requirements.txt
│   ├── graph/
│   │   ├── state.py               # CampaignState TypedDict
│   │   └── campaign_graph.py      # LangGraph graph
│   ├── agents/
│   │   ├── orchestrator.py        # GPT-4o, memory loader
│   │   ├── planner.py             # Campaign strategy
│   │   ├── researcher.py          # Tavily web search
│   │   ├── content_writer.py      # Ad copy generation
│   │   ├── targeting.py           # Audience segments
│   │   ├── critic.py              # Quality review + routing
│   │   └── publisher.py           # LinkedIn + Buffer + episodic save
│   ├── memory/
│   │   ├── memory_manager.py      # Unified interface
│   │   ├── episodic.py            # ChromaDB episodes
│   │   ├── semantic.py            # ChromaDB knowledge
│   │   ├── entity.py              # SQLite entities
│   │   └── procedural.py         # ChromaDB SOPs
│   └── tools/
│       ├── web_search.py          # Tavily
│       ├── linkedin_tool.py       # LinkedIn OAuth2
│       └── buffer_tool.py         # Buffer scheduling
└── frontend/
    ├── app/
    │   ├── page.tsx               # Dashboard
    │   ├── campaign/new/page.tsx  # Campaign creation
    │   └── campaign/[id]/page.tsx # Live view + results
    └── components/
        ├── AgentGraph.tsx         # Pipeline visualization
        ├── AgentFeed.tsx          # Live event stream
        ├── CampaignPreview.tsx    # Content + strategy
        ├── MemoryExplorer.tsx     # 6-memory tabbed view
        └── PublishPanel.tsx       # Publish results
```

---

## Demo Walkthrough

1. Open [localhost:3000](http://localhost:3000) to see the architecture overview
2. Click **Launch New Campaign**
3. Fill in: product name, description, goal, audience, tone, budget
4. Click **Launch Campaign Agent**
5. Watch the **Live Agent Pipeline** as each node activates in sequence
6. Follow the **Agent Feed** to see each agent's reasoning, memory reads, and tool calls
7. The **Critic Agent** may loop back to the Content Writer if quality < 80%
8. Once complete, explore:
   - **Content tab**: 3 ad copy variants + campaign strategy + audience targeting
   - **Memory Explorer**: see all 6 memory systems populated with real data
   - **Publish tab**: LinkedIn post ID and Buffer schedule confirmation
