"use client";

import { useMemo } from "react";
import type { AgentEvent } from "@/lib/types";
import { AGENT_COLORS, AGENT_LABELS } from "@/lib/types";

const NODES = [
  { id: "orchestrator", label: "Orchestrator" },
  { id: "planner", label: "Planner" },
  { id: "researcher", label: "Researcher" },
  { id: "content_writer", label: "Content Writer" },
  { id: "targeting", label: "Targeting" },
  { id: "critic", label: "Critic" },
  { id: "publisher", label: "Publisher" },
];

interface AgentGraphProps {
  activeNode: string | null;
  events: AgentEvent[];
}

export default function AgentGraph({ activeNode, events }: AgentGraphProps) {
  const completedNodes = useMemo(() => {
    const seen = new Set<string>();
    for (const e of events) seen.add(e.agent);
    return seen;
  }, [events]);

  const revisionCount = useMemo(() => {
    return events.filter(
      (e) => e.agent === "content_writer" && (e.revision ?? 0) > 0
    ).length;
  }, [events]);

  return (
    <div
      className="rounded-2xl border p-4 overflow-x-auto"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="flex items-center gap-1 min-w-max">
        {NODES.map((node, i) => {
          const color = AGENT_COLORS[node.id] ?? "#6b7280";
          const icon = AGENT_LABELS[node.id] ?? "AGN";
          const isActive = activeNode === node.id;
          const isDone = completedNodes.has(node.id) && !isActive;
          const isPending = !completedNodes.has(node.id) && !isActive;

          return (
            <div key={node.id} className="flex items-center gap-1">
              <div
                className={`flex flex-col items-center gap-1.5 px-3 py-2.5 rounded-xl border transition-all duration-300 ${
                  isActive ? "agent-active" : ""
                }`}
                style={{
                  borderColor: isActive
                    ? color
                    : isDone
                    ? color + "60"
                    : "var(--border)",
                  background: isActive
                    ? color + "25"
                    : isDone
                    ? color + "12"
                    : "transparent",
                  boxShadow: isActive ? `0 0 16px ${color}50` : "none",
                  minWidth: 80,
                  opacity: isPending ? 0.45 : 1,
                }}
              >
                <div className="relative">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border" style={{ borderColor: color + "40", color }}>
                    {icon}
                  </span>
                  {isActive && (
                    <span
                      className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 animate-pulse"
                      style={{
                        background: color,
                        borderColor: "var(--surface)",
                      }}
                    />
                  )}
                  {isDone && (
                    <span
                      className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full flex items-center justify-center"
                      style={{
                        background: "#10b981",
                        fontSize: 8,
                        color: "white",
                        lineHeight: 1,
                      }}
                    >
                      ✓
                    </span>
                  )}
                </div>
                <span
                  className="text-xs font-medium text-center leading-tight"
                  style={{
                    color: isActive ? color : isDone ? color + "cc" : "var(--text-muted)",
                    fontSize: 10,
                  }}
                >
                  {node.label}
                </span>
              </div>

              {/* Edge arrows */}
              {i < NODES.length - 1 && (
                <div className="flex flex-col items-center gap-0.5 px-1">
                  {i === 5 ? (
                    // Critic → Content Writer revision loop
                    <div className="flex flex-col items-center">
                      <div
                        className="text-xs font-bold"
                        style={{ color: "var(--text-muted)" }}
                      >
                        ↓→
                      </div>
                      {revisionCount > 0 && (
                        <span
                          className="text-xs rounded-full px-1.5"
                          style={{
                            background: "#fef2f2",
                            color: "#dc2626",
                            fontSize: 9,
                          }}
                        >
                          {revisionCount}✕
                        </span>
                      )}
                      <div
                        className="text-xs"
                        style={{ color: "var(--text-muted)", fontSize: 9 }}
                      >
                        &lt;0.8
                      </div>
                    </div>
                  ) : (
                    <div
                      className="text-base font-bold"
                      style={{ color: "var(--border)" }}
                    >
                      →
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
