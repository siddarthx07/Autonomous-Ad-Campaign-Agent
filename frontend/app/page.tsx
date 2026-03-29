"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BACKEND_URL } from "@/lib/utils";
import type { CampaignSession } from "@/lib/types";

const AGENT_NODES = [
  { id: "orchestrator", label: "Orchestrator", icon: "🧠", color: "#6366f1" },
  { id: "planner", label: "Planning Agent", icon: "📋", color: "#8b5cf6" },
  { id: "researcher", label: "Research Agent", icon: "🔍", color: "#06b6d4" },
  { id: "content_writer", label: "Content Writer", icon: "✍️", color: "#10b981" },
  { id: "targeting", label: "Targeting Agent", icon: "🎯", color: "#f59e0b" },
  { id: "critic", label: "Critic Agent", icon: "⚖️", color: "#ef4444" },
  { id: "publisher", label: "Publisher Agent", icon: "🚀", color: "#3b82f6" },
];

const MEMORY_TYPES = [
  { id: "working", label: "Working Memory", desc: "LangGraph in-flight state", color: "#6366f1" },
  { id: "episodic", label: "Episodic Memory", desc: "Past campaign runs", color: "#8b5cf6" },
  { id: "semantic", label: "Semantic Memory", desc: "Platform knowledge base", color: "#06b6d4" },
  { id: "conversation", label: "Conversation History", desc: "User ↔ agent messages", color: "#10b981" },
  { id: "entity", label: "Entity Memory", desc: "Brands, personas, products", color: "#f59e0b" },
  { id: "procedural", label: "Procedural Memory", desc: "SOPs and workflows", color: "#ef4444" },
];

export default function Dashboard() {
  const [sessions, setSessions] = useState<CampaignSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/sessions`)
      .then((r) => r.json())
      .then((d) => setSessions(d.sessions || []))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center py-8">
        <div
          className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border mb-4 font-mono"
          style={{
            color: "var(--accent)",
            borderColor: "var(--accent)",
            background: "rgba(99,102,241,0.1)",
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
          Autonomous AI · LangGraph · GPT-4o · 6 Memory Systems
        </div>
        <h1 className="text-4xl font-bold mb-3" style={{ color: "var(--text)" }}>
          Campaign Agent
        </h1>
        <p className="text-lg max-w-2xl mx-auto mb-6" style={{ color: "var(--text-muted)" }}>
          A multi-agent system that runs end-to-end marketing campaigns — from research to publishing
          — on LinkedIn and Buffer, autonomously.
        </p>
        <Link
          href="/campaign/new"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-white transition-all hover:scale-105"
          style={{
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            boxShadow: "0 0 30px rgba(99,102,241,0.4)",
          }}
        >
          Launch New Campaign
          <span>→</span>
        </Link>
      </div>

      {/* Agent Pipeline */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: "var(--text-muted)" }}>
          Agent Pipeline
        </h2>
        <div
          className="rounded-2xl border p-6 overflow-x-auto"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-2 min-w-max">
            {AGENT_NODES.map((node, i) => (
              <div key={node.id} className="flex items-center gap-2">
                <div
                  className="flex flex-col items-center gap-2 px-4 py-3 rounded-xl border"
                  style={{
                    borderColor: node.color + "40",
                    background: node.color + "15",
                    minWidth: 110,
                  }}
                >
                  <span className="text-2xl">{node.icon}</span>
                  <span className="text-xs font-medium text-center" style={{ color: node.color }}>
                    {node.label}
                  </span>
                </div>
                {i < AGENT_NODES.length - 1 && (
                  <div className="flex flex-col items-center gap-0.5">
                    <div
                      className="text-lg font-bold"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {i === 5 ? "↺" : "→"}
                    </div>
                    {i === 5 && (
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        if &lt;0.8
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Memory Architecture */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: "var(--text-muted)" }}>
          Memory Architecture
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {MEMORY_TYPES.map((mem) => (
            <div
              key={mem.id}
              className="rounded-xl border p-3"
              style={{
                borderColor: mem.color + "40",
                background: mem.color + "10",
              }}
            >
              <div
                className="w-2 h-2 rounded-full mb-2"
                style={{ background: mem.color }}
              />
              <div className="text-xs font-semibold mb-1" style={{ color: mem.color }}>
                {mem.label}
              </div>
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                {mem.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Recent Campaigns */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider mb-4" style={{ color: "var(--text-muted)" }}>
          Recent Campaigns
        </h2>
        {loading ? (
          <div
            className="rounded-2xl border p-8 text-center"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div className="text-sm" style={{ color: "var(--text-muted)" }}>
              Loading...
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div
            className="rounded-2xl border p-8 text-center"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div className="text-3xl mb-3">🚀</div>
            <div className="text-sm font-medium mb-1" style={{ color: "var(--text)" }}>
              No campaigns yet
            </div>
            <div className="text-xs mb-4" style={{ color: "var(--text-muted)" }}>
              Launch your first autonomous campaign to see it here.
            </div>
            <Link
              href="/campaign/new"
              className="text-xs px-4 py-2 rounded-lg font-medium text-white"
              style={{ background: "var(--accent)" }}
            >
              Start Campaign
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((s) => (
              <Link
                key={s.session_id}
                href={`/campaign/${s.session_id}`}
                className="flex items-center justify-between p-4 rounded-xl border hover:border-indigo-500/50 transition-colors"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
              >
                <div>
                  <div className="font-medium text-sm" style={{ color: "var(--text)" }}>
                    {s.product_name}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                    {s.campaign_goal}
                  </div>
                </div>
                <StatusBadge status={s.status} />
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; bg: string }> = {
    published: { color: "#10b981", bg: "rgba(16,185,129,0.1)" },
    running: { color: "#6366f1", bg: "rgba(99,102,241,0.1)" },
    failed: { color: "#ef4444", bg: "rgba(239,68,68,0.1)" },
  };
  const style = map[status] || { color: "var(--text-muted)", bg: "transparent" };
  return (
    <span
      className="text-xs px-2 py-1 rounded-full border font-medium capitalize"
      style={{ color: style.color, borderColor: style.color, background: style.bg }}
    >
      {status}
    </span>
  );
}
