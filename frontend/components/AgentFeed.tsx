"use client";

import { useEffect, useRef } from "react";
import type { AgentEvent } from "@/lib/types";
import { AGENT_COLORS, AGENT_LABELS } from "@/lib/types";
import { cn } from "@/lib/utils";

interface AgentFeedProps {
  events: AgentEvent[];
  isRunning: boolean;
}

const TYPE_ICONS: Record<string, string> = {
  analysis: "ANL",
  strategy: "STR",
  research: "RSH",
  content: "CNT",
  targeting: "TGT",
  critique: "CRQ",
  publish: "PUB",
};

const MEMORY_COLORS: Record<string, string> = {
  episodic: "#0ea5e9",
  semantic: "#0891b2",
  entity: "#d97706",
  procedural: "#dc2626",
  working: "#2563eb",
  conversation: "#16a34a",
};

export default function AgentFeed({ events, isRunning }: AgentFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div
      className="rounded-2xl border"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              isRunning ? "animate-pulse" : ""
            )}
            style={{ background: isRunning ? "var(--accent)" : "var(--success)" }}
          />
          <span className="text-xs font-semibold" style={{ color: "var(--text)" }}>
            Agent Activity
          </span>
        </div>
        <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
          {events.length} events
        </span>
      </div>

      <div
        className="overflow-y-auto p-4 space-y-3"
        style={{ maxHeight: 480 }}
      >
        {events.length === 0 && (
          <div className="text-center py-8">
            {isRunning ? (
              <div className="flex flex-col items-center gap-3">
                <div
                  className="w-8 h-8 border-2 rounded-full animate-spin"
                  style={{
                    borderColor: "var(--border)",
                    borderTopColor: "var(--accent)",
                  }}
                />
                <div className="text-sm cursor-blink" style={{ color: "var(--text-muted)" }}>
                  Agents initialising
                </div>
              </div>
            ) : (
              <div className="text-sm" style={{ color: "var(--text-muted)" }}>
                No events yet
              </div>
            )}
          </div>
        )}

        {events.map((event, i) => (
          <EventCard key={event.id || i} event={event} />
        ))}

        {isRunning && events.length > 0 && (
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-lg"
            style={{ background: "var(--accent-light)" }}
          >
            <div
              className="w-3 h-3 border-2 rounded-full animate-spin flex-shrink-0"
              style={{
                borderColor: "#bfdbfe",
                borderTopColor: "var(--accent)",
              }}
            />
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              Processing...
            </span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function EventCard({ event }: { event: AgentEvent }) {
  const color = AGENT_COLORS[event.agent] ?? "#6b7280";
  const agentIcon = AGENT_LABELS[event.agent] ?? "AGN";
  const typeIcon = TYPE_ICONS[event.type] ?? "EVT";

  return (
    <div
      className="rounded-xl border p-3 space-y-2 fade-in-up"
      style={{
        borderColor: color + "30",
        background: color + "08",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span
            className="text-[10px] flex-shrink-0 px-1.5 py-0.5 rounded border font-semibold font-mono"
            style={{ color: color, borderColor: color + "40", background: color + "10" }}
          >
            {typeIcon}
          </span>
          <div className="min-w-0">
            <div
              className="text-xs font-semibold"
              style={{ color }}
            >
              {agentIcon} {event.agent.replace("_", " ").toUpperCase()}
            </div>
            <div
              className="text-xs font-medium truncate"
              style={{ color: "var(--text)" }}
            >
              {event.title}
            </div>
          </div>
        </div>
        <span
          className="text-xs flex-shrink-0 font-mono"
          style={{ color: "var(--text-muted)" }}
        >
          {new Date(event.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Content */}
      <div
        className="text-xs leading-relaxed whitespace-pre-wrap"
        style={{ color: "var(--text-muted)" }}
      >
        {event.content}
      </div>

      {/* Memory reads/writes */}
      {((event.memory_reads?.length ?? 0) > 0 ||
        (event.memory_writes?.length ?? 0) > 0) && (
        <div className="flex flex-wrap gap-1 pt-1">
          {event.memory_reads?.map((m) => (
            <MemoryBadge key={m} type={m} action="read" />
          ))}
          {event.memory_writes?.map((m) => (
            <MemoryBadge key={m} type={m} action="write" />
          ))}
        </div>
      )}

      {/* Tools used */}
      {(event.tools_used?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {event.tools_used?.map((t) => (
            <span
              key={t}
              className="text-xs px-2 py-0.5 rounded-full border font-mono"
              style={{
                color: "#0891b2",
                borderColor: "#67e8f9",
                background: "#ecfeff",
              }}
            >
              TOOL {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function MemoryBadge({
  type,
  action,
}: {
  type: string;
  action: "read" | "write";
}) {
  const color = MEMORY_COLORS[type] ?? "#6b7280";
  return (
    <span
      className="text-xs px-2 py-0.5 rounded-full border"
      style={{
        color,
        borderColor: color + "30",
        background: color + "10",
      }}
    >
      {action === "read" ? "READ" : "WRITE"} {type}
    </span>
  );
}
