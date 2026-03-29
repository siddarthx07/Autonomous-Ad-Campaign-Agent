"use client";

import { useEffect, useState } from "react";
import type { MemorySnapshot } from "@/lib/types";

interface MemoryExplorerProps {
  sessionId: string;
}

type MemTab =
  | "working"
  | "episodic"
  | "semantic"
  | "conversation"
  | "entity"
  | "procedural";

const MEMORY_CONFIG: Record<
  MemTab,
  { label: string; color: string; icon: string; desc: string }
> = {
  working: {
    label: "Working Memory",
    color: "#6366f1",
    icon: "⚡",
    desc: "LangGraph in-flight state — volatile, discarded after run",
  },
  episodic: {
    label: "Episodic Memory",
    color: "#8b5cf6",
    icon: "🎞️",
    desc: "Past campaign runs stored in ChromaDB — retrieved by similarity",
  },
  semantic: {
    label: "Semantic Memory",
    color: "#06b6d4",
    icon: "📚",
    desc: "Platform knowledge base — LinkedIn specs, copywriting rules",
  },
  conversation: {
    label: "Conversation History",
    color: "#10b981",
    icon: "💬",
    desc: "User ↔ agent message history persisted to SQLite",
  },
  entity: {
    label: "Entity Memory",
    color: "#f59e0b",
    icon: "🏷️",
    desc: "Extracted entities — brands, personas, products in SQLite",
  },
  procedural: {
    label: "Procedural Memory",
    color: "#ef4444",
    icon: "📋",
    desc: "SOPs and workflows stored in ChromaDB — injected into prompts",
  },
};

export default function MemoryExplorer({ sessionId }: MemoryExplorerProps) {
  const [snapshot, setSnapshot] = useState<MemorySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<MemTab>("working");

  useEffect(() => {
    const fetchSnapshot = () => {
      fetch(`/api/memory?session_id=${sessionId}`)
        .then((r) => r.json())
        .then(setSnapshot)
        .catch(console.error)
        .finally(() => setLoading(false));
    };

    fetchSnapshot();
    // Poll every 5s while session is active
    const interval = setInterval(fetchSnapshot, 5000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const cfg = MEMORY_CONFIG[tab];

  return (
    <div
      className="rounded-2xl border"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      {/* Tab bar */}
      <div
        className="flex overflow-x-auto border-b"
        style={{ borderColor: "var(--border)" }}
      >
        {(Object.keys(MEMORY_CONFIG) as MemTab[]).map((t) => {
          const c = MEMORY_CONFIG[t];
          return (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="flex items-center gap-1.5 px-3 py-3 text-xs font-medium whitespace-nowrap border-b-2 transition-colors"
              style={
                tab === t
                  ? { borderColor: c.color, color: c.color }
                  : { borderColor: "transparent", color: "var(--text-muted)" }
              }
            >
              <span>{c.icon}</span>
              <span className="hidden sm:inline">{c.label}</span>
            </button>
          );
        })}
      </div>

      {/* Header */}
      <div className="px-5 py-3 border-b" style={{ borderColor: "var(--border)" }}>
        <div
          className="flex items-center gap-2 text-sm font-semibold"
          style={{ color: cfg.color }}
        >
          <span>{cfg.icon}</span>
          {cfg.label}
        </div>
        <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {cfg.desc}
        </div>
      </div>

      {/* Content */}
      <div className="p-5 overflow-y-auto" style={{ maxHeight: 400 }}>
        {loading ? (
          <div className="flex justify-center py-8">
            <div
              className="w-6 h-6 border-2 rounded-full animate-spin"
              style={{
                borderColor: "var(--border)",
                borderTopColor: "var(--accent)",
              }}
            />
          </div>
        ) : !snapshot ? (
          <EmptyState msg="Could not load memory snapshot." />
        ) : (
          <MemoryContent tab={tab} snapshot={snapshot} />
        )}
      </div>
    </div>
  );
}

function MemoryContent({
  tab,
  snapshot,
}: {
  tab: MemTab;
  snapshot: MemorySnapshot;
}) {
  switch (tab) {
    case "working":
      return <WorkingMemView data={snapshot.working} />;
    case "episodic":
      return <EpisodicView items={snapshot.episodic} />;
    case "semantic":
      return <SemanticView items={snapshot.semantic} />;
    case "conversation":
      return <ConversationView messages={snapshot.conversation} />;
    case "entity":
      return <EntityView entities={snapshot.entity} />;
    case "procedural":
      return <ProceduralView items={snapshot.procedural} />;
    default:
      return null;
  }
}

function WorkingMemView({ data }: { data: Record<string, unknown> }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <EmptyState msg="Working memory is empty — run a campaign to populate it." />
    );
  }
  return (
    <div className="space-y-2">
      {Object.entries(data).map(([k, v]) => (
        <div
          key={k}
          className="flex gap-3 text-xs p-2 rounded-lg"
          style={{ background: "var(--surface-2)" }}
        >
          <span
            className="font-mono font-semibold flex-shrink-0"
            style={{ color: "#6366f1", minWidth: 140 }}
          >
            {k}
          </span>
          <span style={{ color: "var(--text)" }}>
            {typeof v === "object" ? JSON.stringify(v) : String(v)}
          </span>
        </div>
      ))}
    </div>
  );
}

function EpisodicView({
  items,
}: {
  items: Array<{ id: string; preview: string; metadata: Record<string, unknown> }>;
}) {
  if (!items?.length)
    return <EmptyState msg="No episodes stored yet. Run a campaign to create the first one." />;
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.id}
          className="rounded-xl border p-3 space-y-2"
          style={{ borderColor: "#8b5cf640", background: "#8b5cf608" }}
        >
          <div className="text-xs font-mono" style={{ color: "#8b5cf6" }}>
            {item.id}
          </div>
          <div className="text-xs" style={{ color: "var(--text)" }}>
            {item.preview}
          </div>
          {item.metadata && (
            <div className="flex flex-wrap gap-1">
              {Object.entries(item.metadata).map(([k, v]) => (
                <span
                  key={k}
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{ background: "var(--surface-2)", color: "var(--text-muted)" }}
                >
                  {k}: {String(v)}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function SemanticView({ items }: { items: Array<{ id: string; preview: string }> }) {
  if (!items?.length) return <EmptyState msg="No knowledge entries." />;
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.id}
          className="rounded-xl border p-3"
          style={{ borderColor: "#06b6d440", background: "#06b6d408" }}
        >
          <div className="text-xs font-mono mb-1" style={{ color: "#06b6d4" }}>
            {item.id}
          </div>
          <div className="text-xs" style={{ color: "var(--text)" }}>
            {item.preview}
          </div>
        </div>
      ))}
    </div>
  );
}

function ConversationView({
  messages,
}: {
  messages: Array<{ role: string; content: string }>;
}) {
  if (!messages?.length)
    return <EmptyState msg="No conversation history yet." />;
  return (
    <div className="space-y-2">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`rounded-xl p-3 text-xs max-w-[85%] ${
            msg.role === "user" ? "ml-auto" : "mr-auto"
          }`}
          style={{
            background:
              msg.role === "user"
                ? "rgba(99,102,241,0.15)"
                : "var(--surface-2)",
            color: "var(--text)",
          }}
        >
          <div
            className="text-xs font-semibold mb-1 capitalize"
            style={{
              color: msg.role === "user" ? "#a5b4fc" : "#10b981",
            }}
          >
            {msg.role}
          </div>
          <div className="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
        </div>
      ))}
    </div>
  );
}

function EntityView({
  entities,
}: {
  entities: Record<string, Array<{ name: string; attributes: Record<string, unknown> }>>;
}) {
  if (!entities || Object.keys(entities).length === 0)
    return <EmptyState msg="No entities extracted yet." />;

  const colors: Record<string, string> = {
    product: "#10b981",
    campaign_goal: "#6366f1",
    target_audience: "#8b5cf6",
    tone: "#06b6d4",
    budget: "#f59e0b",
    platform: "#3b82f6",
  };

  return (
    <div className="space-y-4">
      {Object.entries(entities).map(([type, items]) => (
        <div key={type}>
          <div
            className="text-xs font-semibold uppercase tracking-wider mb-2"
            style={{ color: colors[type] ?? "var(--text-muted)" }}
          >
            {type.replace(/_/g, " ")}
          </div>
          <div className="flex flex-wrap gap-2">
            {items.map((item) => (
              <span
                key={item.name}
                className="text-xs px-3 py-1.5 rounded-full border font-medium"
                style={{
                  color: colors[type] ?? "var(--text-muted)",
                  borderColor: (colors[type] ?? "#6b7280") + "40",
                  background: (colors[type] ?? "#6b7280") + "10",
                }}
              >
                {item.name}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function ProceduralView({
  items,
}: {
  items: Array<{ id: string; preview: string }>;
}) {
  if (!items?.length) return <EmptyState msg="No procedures loaded." />;
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.id}
          className="rounded-xl border p-3"
          style={{ borderColor: "#ef444440", background: "#ef444408" }}
        >
          <div className="text-xs font-mono mb-1" style={{ color: "#ef4444" }}>
            {item.id}
          </div>
          <div className="text-xs whitespace-pre-wrap" style={{ color: "var(--text)" }}>
            {item.preview}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ msg }: { msg: string }) {
  return (
    <div className="text-center py-8 text-sm" style={{ color: "var(--text-muted)" }}>
      {msg}
    </div>
  );
}
