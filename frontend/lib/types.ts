export interface AdVariant {
  platform: "linkedin_post" | "twitter_post" | "buffer";
  headline: string;
  body: string;
  cta: string;
  image_prompt: string | null;
}

export interface AudienceSegment {
  segment_name: string;
  seniority: string[];
  industries: string[];
  geo: string[];
  interests: string[];
}

export interface CriticScore {
  overall: number;
  engagement: number;
  brand_alignment: number;
  platform_compliance: number;
  feedback: string;
}

export interface CampaignPlan {
  objective: string;
  kpis: string[];
  timeline: string;
  platforms: string[];
  messaging_pillars: string[];
}

export interface PublishResult {
  buffer_update_ids: string[];
  linkedin_ids: string[];
  twitter_ids: string[];
  published_at: string | null;
  errors: string[];
}

export interface AgentEvent {
  id: string;
  timestamp: string;
  agent: string;
  type: string;
  title: string;
  content: string;
  memory_reads?: string[];
  memory_writes?: string[];
  tools_used?: string[];
  data?: unknown;
  revision?: number;
}

export interface SSEMessage {
  type:
    | "start"
    | "agent_event"
    | "node_complete"
    | "complete"
    | "error"
    | "message";
  session_id?: string;
  message?: string;
  event?: AgentEvent;
  node?: string;
  status?: string;
  publish_result?: PublishResult;
  error?: string;
}

export interface CampaignSession {
  session_id: string;
  status: string;
  product_name: string;
  campaign_goal: string;
  published_at: string | null;
}

export interface MemorySnapshot {
  working: Record<string, unknown>;
  episodic: Array<{ id: string; preview: string; metadata: Record<string, unknown> }>;
  semantic: Array<{ id: string; preview: string }>;
  conversation: Array<{ role: string; content: string }>;
  entity: Record<string, Array<{ name: string; attributes: Record<string, unknown> }>>;
  procedural: Array<{ id: string; preview: string }>;
}

export const AGENT_COLORS: Record<string, string> = {
  orchestrator: "#2563eb",
  planner: "#0891b2",
  researcher: "#0d9488",
  content_writer: "#16a34a",
  targeting: "#d97706",
  critic: "#dc2626",
  publisher: "#0369a1",
};

export const AGENT_LABELS: Record<string, string> = {
  orchestrator: "ORC",
  planner: "PLN",
  researcher: "RES",
  content_writer: "CW",
  targeting: "TGT",
  critic: "CRT",
  publisher: "PUB",
};

/** @deprecated Use AGENT_LABELS instead — no emojis */
export const AGENT_ICONS = AGENT_LABELS;
