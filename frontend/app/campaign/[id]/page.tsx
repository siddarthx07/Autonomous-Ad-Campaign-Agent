"use client";

import { useEffect, useRef, useState } from "react";
import { use } from "react";
import type { AgentEvent, SSEMessage } from "@/lib/types";
import AgentFeed from "@/components/AgentFeed";
import CampaignResults from "@/components/CampaignResults";
import { BACKEND_URL } from "@/lib/utils";

export default function CampaignPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: sessionId } = use(params);

  const [isRunning, setIsRunning] = useState(true);
  const [liveEvents, setLiveEvents] = useState<AgentEvent[]>([]);
  const [finalState, setFinalState] = useState<Record<string, unknown> | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/campaign/${sessionId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.status && data.status !== "running") {
          setFinalState(data);
          setIsRunning(false);
          return;
        }

        const es = new EventSource(
          `${BACKEND_URL}/api/campaign/stream?session_id=${sessionId}`
        );
        eventSourceRef.current = es;

        es.addEventListener("agent_event", (e) => {
          const msg: SSEMessage = JSON.parse(e.data);
          if (msg.event) {
            setLiveEvents((prev) => [...prev, msg.event as AgentEvent]);
          }
        });

        es.addEventListener("complete", async () => {
          try {
            const resp = await fetch(`${BACKEND_URL}/api/campaign/${sessionId}`);
            const completed = await resp.json();
            setFinalState(completed);
          } catch {
            setFinalState({ status: "done" });
          }
          setIsRunning(false);
          es.close();
        });

        es.addEventListener("error", () => {
          fetch(`${BACKEND_URL}/api/campaign/${sessionId}`)
            .then((r) => r.json())
            .then((data) => {
              if (data.status && data.status !== "running") {
                setFinalState(data);
                setIsRunning(false);
              }
            })
            .catch(() => {});
          es.close();
        });

        es.onerror = () => es.close();
      })
      .catch(() => setIsRunning(false));

    return () => eventSourceRef.current?.close();
  }, [sessionId]);

  const productName =
    (finalState?.product_name as string) || sessionId.slice(0, 8) + "...";
  const campaignGoal = (finalState?.campaign_goal as string) || "";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1
            className="text-lg font-semibold tracking-tight"
            style={{ color: "var(--text)" }}
          >
            {productName}
          </h1>
          {campaignGoal && (
            <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              {campaignGoal}
            </p>
          )}
          <p
            className="text-[11px] font-mono mt-1"
            style={{ color: "var(--text-muted)", opacity: 0.5 }}
          >
            {sessionId}
          </p>
        </div>

        {isRunning ? (
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium"
            style={{
              color: "var(--accent)",
              borderColor: "#bfdbfe",
              background: "var(--accent-light)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: "var(--accent)" }}
            />
            Running
          </div>
        ) : (
          <span
            className="text-xs px-2.5 py-1 rounded-full border font-medium"
            style={{
              color: "var(--success)",
              borderColor: "#bbf7d0",
              background: "var(--success-light)",
            }}
          >
            Published
          </span>
        )}
      </div>

      {isRunning && (
        <AgentFeed events={liveEvents} isRunning={isRunning} />
      )}

      {!isRunning && finalState && (
        <CampaignResults sessionId={sessionId} finalState={finalState} />
      )}
    </div>
  );
}
