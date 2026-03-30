"use client";

import type { AdVariant, PublishResult, CriticScore } from "@/lib/types";
import MemoryExplorer from "@/components/MemoryExplorer";

interface Lessons {
  best_tones?: string[];
  avoid_tones?: string[];
  top_pillars?: string[];
  best_ctas?: string[];
  top_score?: number;
  lesson_summary?: string;
}

interface Props {
  sessionId: string;
  finalState: Record<string, unknown>;
}

const PLATFORM_META = {
  linkedin: { label: "LinkedIn", icon: "LI", color: "#0369a1" },
  twitter: { label: "X / Twitter", icon: "X", color: "#0284c7" },
};

export default function CampaignResults({ sessionId, finalState }: Props) {
  const publishResult = finalState.publish_result as PublishResult | null;
  const adVariants = (finalState.ad_variants as AdVariant[]) || [];
  const criticScore = finalState.critic_score as CriticScore | null;
  const lessons = (finalState.campaign_lessons as Lessons) || {};

  const publishedAt = publishResult?.published_at
    ? new Date(publishResult.published_at).toLocaleString()
    : null;

  return (
    <div className="space-y-5">
      {/* Published header */}
      <div
        className="rounded-2xl border p-5"
        style={{ background: "var(--success-light)", borderColor: "#bbf7d0" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
            style={{ background: "#dcfce7" }}
          >
            OK
          </div>
          <div>
            <div className="font-semibold" style={{ color: "var(--success)" }}>
              Campaign Published
            </div>
            {publishedAt && (
              <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                {publishedAt}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ad copy reference */}
      {adVariants.length > 0 && (
        <section>
          <h3
            className="text-xs font-semibold uppercase tracking-wider mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Generated Copy
          </h3>
          <div className="space-y-3">
            {adVariants.map((v, i) => {
              const meta =
                PLATFORM_META[
                  v.platform === "linkedin_post" ? "linkedin" : "twitter"
                ] || PLATFORM_META.linkedin;
              return (
                <div
                  key={i}
                  className="rounded-2xl border p-4"
                  style={{
                    background: "var(--surface)",
                    borderColor: "var(--border)",
                  }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border" style={{ borderColor: meta.color + "40", color: meta.color }}>
                      {meta.icon}
                    </span>
                    <span
                      className="text-xs font-semibold"
                      style={{ color: meta.color }}
                    >
                      {meta.label}
                    </span>
                  </div>
                  <div
                    className="font-semibold text-sm mb-1"
                    style={{ color: "var(--text)" }}
                  >
                    {v.headline}
                  </div>
                  <div
                    className="text-xs leading-relaxed mb-2"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {v.body}
                  </div>
                  <div
                    className="text-xs font-semibold"
                    style={{ color: meta.color }}
                  >
                    → {v.cta}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Critic score */}
      {criticScore && (
        <section>
          <h3
            className="text-xs font-semibold uppercase tracking-wider mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Critic Score
          </h3>
          <div
            className="rounded-2xl border p-4 space-y-3"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-3">
              <div
                className="text-2xl font-bold tabular-nums"
                style={{
                  color:
                    criticScore.overall >= 0.75
                      ? "#10b981"
                      : criticScore.overall >= 0.55
                      ? "#f59e0b"
                      : "#ef4444",
                }}
              >
                {Math.round(criticScore.overall * 100)}
                <span className="text-sm font-normal">/100</span>
              </div>
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                Overall quality score
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  ["Engagement", criticScore.engagement],
                  ["Brand Fit", criticScore.brand_alignment],
                  ["Platform", criticScore.platform_compliance],
                ] as [string, number][]
              ).map(([label, val]) => (
                <div
                  key={label}
                  className="rounded-xl p-2 text-center"
                  style={{ background: "var(--surface-hover)" }}
                >
                  <div
                    className="text-sm font-semibold"
                    style={{ color: "var(--text)" }}
                  >
                    {Math.round(val * 100)}
                  </div>
                  <div
                    className="text-xs mt-0.5"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {label}
                  </div>
                </div>
              ))}
            </div>
            {criticScore.feedback && (
              <div
                className="text-xs leading-relaxed border-t pt-3"
                style={{ color: "var(--text-muted)", borderColor: "var(--border)" }}
              >
                {criticScore.feedback}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Lessons applied this run */}
      {lessons.lesson_summary && !lessons.lesson_summary.startsWith("No past") && (
        <section>
          <h3
            className="text-xs font-semibold uppercase tracking-wider mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Lessons Applied From Memory
          </h3>
          <div
            className="rounded-2xl border p-4"
            style={{ background: "#eff6ff", borderColor: "#bfdbfe" }}
          >
            <div className="flex items-start gap-3">
              <span className="text-[11px] font-mono mt-0.5 px-1.5 py-0.5 rounded border" style={{ borderColor: "#93c5fd", color: "#2563eb" }}>MEM</span>
              <div className="space-y-1.5">
                {lessons.lesson_summary.split("\n").map((line, i) => (
                  <div
                    key={i}
                    className="text-xs leading-relaxed"
                    style={{ color: "var(--text)" }}
                  >
                    {line}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* What this campaign teaches future runs */}
      <section>
        <h3
          className="text-xs font-semibold uppercase tracking-wider mb-3"
          style={{ color: "var(--text-muted)" }}
        >
          What the System Learned This Run
        </h3>
        <div
          className="rounded-2xl border p-4 space-y-2"
            style={{ background: "#f0f9ff", borderColor: "#bae6fd" }}
        >
          <div className="flex items-start gap-3">
            <span className="text-[11px] font-mono mt-0.5 px-1.5 py-0.5 rounded border" style={{ borderColor: "#7dd3fc", color: "#0284c7" }}>LOG</span>
            <div className="space-y-1.5 flex-1">
              <div className="text-xs" style={{ color: "var(--text)" }}>
                This run has been saved to{" "}
                <span style={{ color: "#0284c7" }}>Episodic Memory</span>.
              </div>
              {criticScore && (
                <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Score recorded:{" "}
                  <span style={{ color: "var(--text)" }}>
                    {Math.round(criticScore.overall * 100)}/100
                  </span>
                  {" "}— tone, messaging pillars, and CTAs from this campaign will
                  influence recommendations for similar future campaigns.
                </div>
              )}
              <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                Next time a similar product/goal is run, the system will say:
              </div>
              <div
                className="rounded-lg px-3 py-2 text-xs font-mono"
                style={{
                  background: "var(--surface)",
                  color: "#0284c7",
                  border: "1px solid #bae6fd",
                }}
              >
                {criticScore
                  ? `"Previous run scored ${Math.round(criticScore.overall * 100)}/100 — apply those tone & pillar choices"`
                  : `"Reference this campaign's structure for similar goals"`}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Memory Systems */}
      <section>
        <h3
          className="text-xs font-semibold uppercase tracking-wider mb-3"
          style={{ color: "var(--text-muted)" }}
        >
          Memory Systems
        </h3>
        <MemoryExplorer sessionId={sessionId} />
      </section>
    </div>
  );
}

