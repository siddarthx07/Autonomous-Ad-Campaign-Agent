"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BACKEND_URL } from "@/lib/utils";
import type { CampaignSession } from "@/lib/types";

const AGENT_NODES = [
  { id: "orchestrator", label: "Orchestrator", abbr: "ORC", color: "#2563eb" },
  { id: "planner", label: "Planning Agent", abbr: "PLN", color: "#0891b2" },
  { id: "researcher", label: "Research Agent", abbr: "RES", color: "#0d9488" },
  { id: "content_writer", label: "Content Writer", abbr: "CW", color: "#16a34a" },
  { id: "targeting", label: "Targeting Agent", abbr: "TGT", color: "#d97706" },
  { id: "critic", label: "Critic Agent", abbr: "CRT", color: "#dc2626" },
  { id: "publisher", label: "Publisher Agent", abbr: "PUB", color: "#0369a1" },
];

const MEMORY_TYPES = [
  { id: "working", label: "Working Memory", desc: "LangGraph in-flight state", color: "#2563eb" },
  { id: "episodic", label: "Episodic Memory", desc: "Past campaign runs", color: "#0891b2" },
  { id: "semantic", label: "Semantic Memory", desc: "Platform knowledge base", color: "#0d9488" },
  { id: "conversation", label: "Conversation History", desc: "User and agent messages", color: "#16a34a" },
  { id: "entity", label: "Entity Memory", desc: "Brands, personas, products", color: "#d97706" },
  { id: "procedural", label: "Procedural Memory", desc: "SOPs and workflows", color: "#dc2626" },
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
    <div className="space-y-10">
      {/* Hero */}
      <div className="text-center py-10 max-w-3xl mx-auto">
        <div
          className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border mb-5 font-mono font-medium"
          style={{
            color: "var(--accent)",
            borderColor: "#bfdbfe",
            background: "var(--accent-light)",
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
          Autonomous AI · LangGraph · GPT-4o · 6 Memory Systems
        </div>
        <h1
          className="text-4xl font-bold mb-4 tracking-tight"
          style={{ color: "var(--text)" }}
        >
          Campaign Agent
        </h1>
        <p
          className="text-base max-w-xl mx-auto mb-8 leading-relaxed"
          style={{ color: "var(--text-muted)" }}
        >
          A multi-agent system that runs end-to-end marketing campaigns — from
          research to publishing — on LinkedIn and X, autonomously.
        </p>
        <Link
          href="/campaign/new"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm text-white transition-all hover:opacity-90"
          style={{
            background: "var(--accent)",
            boxShadow: "0 1px 3px rgba(37,99,235,0.3), 0 4px 12px rgba(37,99,235,0.15)",
          }}
        >
          Launch New Campaign
          <span className="text-base leading-none">→</span>
        </Link>
      </div>

      {/* Agent Pipeline */}
      <section>
        <h2
          className="text-xs font-semibold uppercase tracking-widest mb-4"
          style={{ color: "var(--text-muted)" }}
        >
          Agent Pipeline
        </h2>
        <div
          className="rounded-xl border p-5 overflow-x-auto"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div className="flex w-full justify-center">
            <div className="flex items-center gap-2 min-w-max">
              {AGENT_NODES.map((node, i) => (
                <div key={node.id} className="flex items-center gap-2">
                  <div
                    className="flex flex-col items-center gap-2 px-4 py-3 rounded-lg border"
                    style={{
                      borderColor: node.color + "30",
                      background: node.color + "0a",
                      minWidth: 108,
                    }}
                  >
                    <div
                      className="w-8 h-8 rounded-md flex items-center justify-center text-xs font-bold text-white"
                      style={{ background: node.color }}
                    >
                      {node.abbr}
                    </div>
                    <span
                      className="text-xs font-medium text-center leading-tight"
                      style={{ color: node.color }}
                    >
                      {node.label}
                    </span>
                  </div>
                  {i < AGENT_NODES.length - 1 && (
                    <div className="flex flex-col items-center gap-0.5">
                      <span
                        className="text-base font-medium"
                        style={{ color: "var(--border-strong)" }}
                      >
                        {i === 5 ? "↺" : "→"}
                      </span>
                      {i === 5 && (
                        <span
                          className="text-xs"
                          style={{ color: "var(--text-muted)", fontSize: 10 }}
                        >
                          if &lt;0.8
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Memory Architecture */}
      <section>
        <h2
          className="text-xs font-semibold uppercase tracking-widest mb-4"
          style={{ color: "var(--text-muted)" }}
        >
          Memory Architecture
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {MEMORY_TYPES.map((mem) => (
            <div
              key={mem.id}
              className="rounded-lg border p-3"
              style={{
                borderColor: mem.color + "25",
                background: mem.color + "06",
              }}
            >
              <div
                className="w-2 h-2 rounded-full mb-2"
                style={{ background: mem.color }}
              />
              <div
                className="text-xs font-semibold mb-1"
                style={{ color: mem.color }}
              >
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
        <h2
          className="text-xs font-semibold uppercase tracking-widest mb-4"
          style={{ color: "var(--text-muted)" }}
        >
          Recent Campaigns
        </h2>
        {loading ? (
          <div
            className="rounded-xl border p-8 text-center"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div className="text-sm" style={{ color: "var(--text-muted)" }}>
              Loading...
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div
            className="rounded-xl border p-10 text-center"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div
              className="text-sm font-semibold mb-2"
              style={{ color: "var(--text)" }}
            >
              No campaigns yet
            </div>
            <div className="text-xs mb-5" style={{ color: "var(--text-muted)" }}>
              Launch your first autonomous campaign to see it here.
            </div>
            <Link
              href="/campaign/new"
              className="inline-flex items-center gap-1.5 text-xs px-4 py-2 rounded-lg font-semibold text-white"
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
                className="flex items-center justify-between p-4 rounded-xl border transition-all"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLAnchorElement).style.borderColor =
                    "#bfdbfe";
                  (e.currentTarget as HTMLAnchorElement).style.boxShadow =
                    "0 1px 6px rgba(0,0,0,0.06)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLAnchorElement).style.borderColor =
                    "var(--border)";
                  (e.currentTarget as HTMLAnchorElement).style.boxShadow =
                    "none";
                }}
              >
                <div>
                  <div
                    className="font-medium text-sm"
                    style={{ color: "var(--text)" }}
                  >
                    {s.product_name}
                  </div>
                  <div
                    className="text-xs mt-0.5"
                    style={{ color: "var(--text-muted)" }}
                  >
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
  const map: Record<string, { color: string; bg: string; border: string }> = {
    published: { color: "#16a34a", bg: "#f0fdf4", border: "#bbf7d0" },
    running: { color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe" },
    failed: { color: "#dc2626", bg: "#fef2f2", border: "#fecaca" },
  };
  const style = map[status] || {
    color: "var(--text-muted)",
    bg: "var(--surface-2)",
    border: "var(--border)",
  };
  return (
    <span
      className="text-xs px-2.5 py-1 rounded-full border font-medium capitalize"
      style={{
        color: style.color,
        borderColor: style.border,
        background: style.bg,
      }}
    >
      {status}
    </span>
  );
}
