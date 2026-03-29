export interface AdVariant {
  platform: "linkedin_post" | "linkedin_ad" | "buffer";
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
  budget_allocation: Record<string, string>;
}

export interface PublishResult {
  linkedin_post_id: string | null;
  linkedin_ad_id: string | null;
  buffer_update_ids: string[];
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
  orchestrator: "#6366f1",
  planner: "#8b5cf6",
  researcher: "#06b6d4",
  content_writer: "#10b981",
  targeting: "#f59e0b",
  critic: "#ef4444",
  publisher: "#3b82f6",
};

export const AGENT_ICONS: Record<string, string> = {
  orchestrator: "🧠",
  planner: "📋",
  researcher: "🔍",
  content_writer: "✍️",
  targeting: "🎯",
  critic: "⚖️",
  publisher: "🚀",
};
