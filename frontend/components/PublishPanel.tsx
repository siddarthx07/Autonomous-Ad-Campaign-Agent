"use client";

import type { AdVariant, PublishResult } from "@/lib/types";

interface PublishPanelProps {
  publishResult: PublishResult | null;
  adVariants: AdVariant[];
}

export default function PublishPanel({
  publishResult,
  adVariants,
}: PublishPanelProps) {
  if (!publishResult) {
    return (
      <div
        className="rounded-2xl border p-8 text-center"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="text-3xl mb-3">⏳</div>
        <div className="text-sm" style={{ color: "var(--text-muted)" }}>
          Campaign not yet published. Waiting for agent to complete.
        </div>
      </div>
    );
  }

  const linkedinCount = publishResult.linkedin_ids?.length ?? 0;
  const twitterCount = publishResult.twitter_ids?.length ?? 0;
  const totalPosts = publishResult.buffer_update_ids?.length ?? 0;
  const hasErrors = publishResult.errors?.length > 0;
  const isSuccess = totalPosts > 0;

  const linkedInVariants = adVariants.filter(
    (v) => v.platform === "linkedin_post" || v.platform === "buffer"
  );
  const twitterVariants = adVariants.filter((v) => v.platform === "twitter_post");

  return (
    <div className="space-y-4">
      {/* Status summary */}
      <div
        className="rounded-2xl border p-5"
        style={{
          background: isSuccess ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
          borderColor: isSuccess ? "#10b98140" : "#ef444440",
        }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
            style={{ background: isSuccess ? "#10b98120" : "#ef444420" }}
          >
            {isSuccess ? "🚀" : "⚠️"}
          </div>
          <div>
            <div className="font-semibold" style={{ color: isSuccess ? "#10b981" : "#ef4444" }}>
              {isSuccess ? "Campaign Published Successfully" : "Publish Issues Detected"}
            </div>
            {publishResult.published_at && (
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                {new Date(publishResult.published_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <StatusCard
            icon="💼"
            label="LinkedIn Posts"
            value={linkedinCount > 0 ? `${linkedinCount} published` : "Not posted"}
            success={linkedinCount > 0}
          />
          <StatusCard
            icon="𝕏"
            label="X / Twitter Posts"
            value={twitterCount > 0 ? `${twitterCount} published` : "Not posted"}
            success={twitterCount > 0}
          />
          <StatusCard
            icon="🔔"
            label="Errors"
            value={hasErrors ? `${publishResult.errors.length} error(s)` : "None"}
            success={!hasErrors}
          />
        </div>
      </div>

      {/* Errors */}
      {hasErrors && (
        <div
          className="rounded-2xl border p-4 space-y-2"
          style={{ background: "rgba(239,68,68,0.08)", borderColor: "#ef444440" }}
        >
          <div className="text-xs font-semibold" style={{ color: "#ef4444" }}>
            Errors
          </div>
          {publishResult.errors.map((err, i) => (
            <div
              key={i}
              className="text-xs px-3 py-2 rounded-lg"
              style={{ background: "rgba(239,68,68,0.1)", color: "var(--text)" }}
            >
              {err}
            </div>
          ))}
        </div>
      )}

      {/* LinkedIn posts */}
      {linkedinCount > 0 && (
        <div
          className="rounded-2xl border p-5"
          style={{ background: "var(--surface)", borderColor: "#0077b540" }}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">💼</span>
            <div>
              <div className="text-sm font-semibold" style={{ color: "#0077b5" }}>
                LinkedIn — Autonomous Campaign Agent
              </div>
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                {linkedinCount} post{linkedinCount > 1 ? "s" : ""} published via Buffer
              </div>
            </div>
          </div>
          <div className="space-y-2">
            {publishResult.linkedin_ids.map((id, i) => (
              <div
                key={id}
                className="flex items-center justify-between p-3 rounded-xl"
                style={{ background: "rgba(0,119,181,0.08)" }}
              >
                <div>
                  <div className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                    Post ID: {id}
                  </div>
                  {linkedInVariants[i] && (
                    <div className="text-xs mt-1 line-clamp-1" style={{ color: "var(--text)" }}>
                      {linkedInVariants[i].headline}
                    </div>
                  )}
                </div>
                <span className="text-xs px-2 py-1 rounded-full" style={{ background: "#10b98120", color: "#10b981" }}>
                  ✓ Live
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* X / Twitter posts */}
      {twitterCount > 0 && (
        <div
          className="rounded-2xl border p-5"
          style={{ background: "var(--surface)", borderColor: "#1d9bf040" }}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">𝕏</span>
            <div>
              <div className="text-sm font-semibold" style={{ color: "#1d9bf0" }}>
                X / Twitter — @siddarth1289300
              </div>
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                {twitterCount} post{twitterCount > 1 ? "s" : ""} published via Buffer
              </div>
            </div>
          </div>
          <div className="space-y-2">
            {publishResult.twitter_ids.map((id, i) => (
              <div
                key={id}
                className="flex items-center justify-between p-3 rounded-xl"
                style={{ background: "rgba(29,155,240,0.08)" }}
              >
                <div>
                  <div className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                    Post ID: {id}
                  </div>
                  {twitterVariants[i] && (
                    <div className="text-xs mt-1 line-clamp-1" style={{ color: "var(--text)" }}>
                      {twitterVariants[i].headline}
                    </div>
                  )}
                </div>
                <span className="text-xs px-2 py-1 rounded-full" style={{ background: "#10b98120", color: "#10b981" }}>
                  ✓ Live
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Episodic memory note */}
      <div
        className="rounded-xl border p-3 flex items-center gap-3"
        style={{ borderColor: "#8b5cf640", background: "#8b5cf608" }}
      >
        <span className="text-lg">🎞️</span>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>
          This campaign has been saved to{" "}
          <span style={{ color: "#8b5cf6" }}>Episodic Memory</span>. Future
          campaigns for similar products will reference these results as context.
        </div>
      </div>
    </div>
  );
}

function StatusCard({
  icon,
  label,
  value,
  success,
}: {
  icon: string;
  label: string;
  value: string;
  success: boolean;
}) {
  return (
    <div
      className="rounded-xl p-3"
      style={{
        background: success ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
        border: `1px solid ${success ? "#10b98130" : "#ef444430"}`,
      }}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <span>{icon}</span>
        <span className="text-xs font-medium" style={{ color: success ? "#10b981" : "#ef4444" }}>
          {label}
        </span>
      </div>
      <div className="text-xs font-mono truncate" style={{ color: "var(--text-muted)" }}>
        {value}
      </div>
    </div>
  );
}
