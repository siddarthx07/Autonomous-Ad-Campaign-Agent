"use client";

import { useEffect, useRef, useState } from "react";
import { use } from "react";
import type { AgentEvent, SSEMessage } from "@/lib/types";
import AgentFeed from "@/components/AgentFeed";
import AgentGraph from "@/components/AgentGraph";
import CampaignPreview from "@/components/CampaignPreview";
import MemoryExplorer from "@/components/MemoryExplorer";
import PublishPanel from "@/components/PublishPanel";
import { BACKEND_URL } from "@/lib/utils";

type Tab = "live" | "content" | "memory" | "publish";

export default function CampaignPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: sessionId } = use(params);

  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [status, setStatus] = useState<"running" | "done" | "error">("running");
  const [finalState, setFinalState] = useState<Record<string, unknown> | null>(null);
  const [tab, setTab] = useState<Tab>("live");
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource(`/api/stream?session_id=${sessionId}`);
    eventSourceRef.current = es;

    es.addEventListener("start", () => {
      setStatus("running");
    });

    es.addEventListener("agent_event", (e) => {
      const msg: SSEMessage = JSON.parse(e.data);
      if (msg.event) {
        setEvents((prev) => [...prev, msg.event!]);
        setActiveNode(msg.event.agent);
      }
    });

    es.addEventListener("node_complete", (e) => {
      const msg: SSEMessage = JSON.parse(e.data);
      if (msg.node) setActiveNode(msg.node);
    });

    es.addEventListener("complete", async (e) => {
      const msg: SSEMessage = JSON.parse(e.data);
      setStatus("done");
      setActiveNode(null);

      // Fetch full final state
      try {
        const resp = await fetch(`${BACKEND_URL}/api/campaign/${sessionId}`);
        const data = await resp.json();
        setFinalState(data);
        if (msg.publish_result) setTab("publish");
        else setTab("content");
      } catch {
        setFinalState({ status: msg.status });
      }

      es.close();
    });

    es.addEventListener("error", (e) => {
      console.error("SSE error", e);
      setStatus("error");
      es.close();
    });

    es.onerror = () => {
      setStatus((prev) => (prev === "running" ? "error" : prev));
      es.close();
    };

    return () => {
      es.close();
    };
  }, [sessionId]);

  const TABS: { id: Tab; label: string; disabled?: boolean }[] = [
    { id: "live", label: "Live Feed" },
    { id: "content", label: "Content", disabled: !finalState },
    { id: "memory", label: "Memory Explorer" },
    { id: "publish", label: "Publish", disabled: !finalState },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
            Campaign Run
          </h1>
          <p className="text-xs font-mono mt-0.5" style={{ color: "var(--text-muted)" }}>
            {sessionId}
          </p>
        </div>
        <StatusIndicator status={status} eventsCount={events.length} />
      </div>

      {/* Agent Graph visualization */}
      <AgentGraph activeNode={activeNode} events={events} />

      {/* Tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: "var(--border)" }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => !t.disabled && setTab(t.id)}
            disabled={t.disabled}
            className="px-4 py-2.5 text-sm font-medium border-b-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            style={
              tab === t.id
                ? { borderColor: "var(--accent)", color: "var(--accent)" }
                : { borderColor: "transparent", color: "var(--text-muted)" }
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {tab === "live" && (
          <AgentFeed events={events} isRunning={status === "running"} />
        )}
        {tab === "content" && finalState && (
          <CampaignPreview
            adVariants={(finalState.ad_variants as never[]) || []}
            campaignPlan={finalState.campaign_plan as never}
            audienceSegments={(finalState.audience_segments as never[]) || []}
            criticScore={finalState.critic_score as never}
            researchFindings={(finalState.research_findings as string) || ""}
          />
        )}
        {tab === "memory" && (
          <MemoryExplorer sessionId={sessionId} />
        )}
        {tab === "publish" && finalState && (
          <PublishPanel
            publishResult={finalState.publish_result as never}
            adVariants={(finalState.ad_variants as never[]) || []}
          />
        )}
      </div>
    </div>
  );
}

function StatusIndicator({
  status,
  eventsCount,
}: {
  status: string;
  eventsCount: number;
}) {
  const cfg = {
    running: { color: "#6366f1", label: "Running", pulse: true },
    done: { color: "#10b981", label: "Complete", pulse: false },
    error: { color: "#ef4444", label: "Error", pulse: false },
  }[status] || { color: "var(--text-muted)", label: status, pulse: false };

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
        {eventsCount} events
      </span>
      <div
        className="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium"
        style={{
          color: cfg.color,
          borderColor: cfg.color + "60",
          background: cfg.color + "15",
        }}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full ${cfg.pulse ? "animate-pulse" : ""}`}
          style={{ background: cfg.color }}
        />
        {cfg.label}
      </div>
    </div>
  );
}
