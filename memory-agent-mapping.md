# Memory Stores and Agent Links

## What each memory stores

### Working Memory (LangGraph state)
Stores in-flight run data: brief, strategy draft, research notes, generated copy, scores, routing flags.  
Ephemeral (for current execution).

### Episodic Memory (ChromaDB)
Stores past campaign run snapshots/outcomes (what worked, scores, successful patterns).  
Retrieved by similarity for future runs.

### Semantic Memory (ChromaDB)
Stores stable domain knowledge: platform rules/specs, best practices, copywriting guidance.  
Reused across all campaigns.

### Conversation Memory (SQLite)
Stores user ↔ system interaction history per session/thread.

### Entity Memory (SQLite)
Stores extracted structured entities: product, brand, audience attributes, tone, campaign metadata.

### Procedural Memory (ChromaDB)
Stores SOPs/workflows/checklists (how to plan, write, review, publish).

## Link between memories and agents

- **Orchestrator/Coordinator**: reads all relevant memories at start; writes updated run context to Working.
- **Strategist**: reads Semantic + Procedural (+ Episodic context), writes plan to Working.
- **Researcher**: reads Working/Entity context, enriches findings into Working (and sometimes Entity).
- **Content Writer**: reads Working + Semantic + Procedural (+ Episodic cues), writes draft variants to Working.
- **Targeting Agent**: reads Working + Entity + Episodic patterns, writes audience segments to Working/Entity.
- **Critic Agent**: reads Working + Semantic rules, writes score/feedback to Working (triggers rewrite loop if low).
- **Publisher**: reads final Working output, publishes externally, then writes campaign summary/outcome to Episodic; logs conversation/entity updates to SQLite stores.
