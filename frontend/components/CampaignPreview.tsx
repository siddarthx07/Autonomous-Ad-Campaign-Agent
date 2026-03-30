"use client";

import { useState } from "react";
import type { AdVariant, AudienceSegment, CampaignPlan, CriticScore } from "@/lib/types";

interface CampaignPreviewProps {
  adVariants: AdVariant[];
  campaignPlan: CampaignPlan | null;
  audienceSegments: AudienceSegment[];
  criticScore: CriticScore | null;
  researchFindings: string;
}

const PLATFORM_CONFIG: Record<
  string,
  { label: string; icon: string; color: string; bg: string }
> = {
  linkedin_post: {
    label: "LinkedIn Post",
    icon: "LI",
    color: "#0369a1",
    bg: "#e0f2fe",
  },
  linkedin_ad: {
    label: "LinkedIn Ad",
    icon: "AD",
    color: "#0284c7",
    bg: "#e0f2fe",
  },
  buffer: {
    label: "Buffer Post",
    icon: "BUF",
    color: "#0891b2",
    bg: "#ecfeff",
  },
};

type Section = "variants" | "strategy" | "targeting" | "research";

export default function CampaignPreview({
  adVariants,
  campaignPlan,
  audienceSegments,
  criticScore,
  researchFindings,
}: CampaignPreviewProps) {
  const [section, setSection] = useState<Section>("variants");

  const SECTIONS: { id: Section; label: string }[] = [
    { id: "variants", label: `Ad Copy (${adVariants.length})` },
    { id: "strategy", label: "Strategy" },
    { id: "targeting", label: `Audience (${audienceSegments.length})` },
    { id: "research", label: "Research" },
  ];

  return (
    <div className="space-y-4">
      {/* Critic Score Banner */}
      {criticScore && <CriticScoreBanner score={criticScore} />}

      {/* Section tabs */}
      <div className="flex gap-2 flex-wrap">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => setSection(s.id)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
            style={
              section === s.id
                ? {
                    background: "var(--accent-light)",
                    borderColor: "#bfdbfe",
                    color: "var(--accent)",
                  }
                : {
                    background: "transparent",
                    borderColor: "var(--border)",
                    color: "var(--text-muted)",
                  }
            }
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Ad Variants */}
      {section === "variants" && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {adVariants.map((v, i) => (
            <AdVariantCard key={i} variant={v} />
          ))}
          {adVariants.length === 0 && (
            <EmptyState msg="No ad variants generated yet." />
          )}
        </div>
      )}

      {/* Strategy */}
      {section === "strategy" && (
        <div className="space-y-4">
          {campaignPlan ? (
            <>
              <InfoCard title="Objective" content={campaignPlan.objective} />
              <div className="grid gap-4 md:grid-cols-2">
                <ListCard title="KPIs" items={campaignPlan.kpis} color="#10b981" />
                <ListCard
                  title="Messaging Pillars"
                  items={campaignPlan.messaging_pillars}
                  color="#0284c7"
                />
              </div>
              <InfoCard title="Timeline" content={campaignPlan.timeline} />
            </>
          ) : (
            <EmptyState msg="Campaign plan not available." />
          )}
        </div>
      )}

      {/* Audience */}
      {section === "targeting" && (
        <div className="space-y-4">
          {audienceSegments.map((seg, i) => (
            <AudienceCard key={i} segment={seg} />
          ))}
          {audienceSegments.length === 0 && (
            <EmptyState msg="No audience segments defined yet." />
          )}
        </div>
      )}

      {/* Research */}
      {section === "research" && (
        <div
          className="rounded-2xl border p-5"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div
            className="text-xs font-semibold mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Research Findings
          </div>
          {researchFindings ? (
            <pre
              className="text-xs leading-relaxed whitespace-pre-wrap"
              style={{ color: "var(--text)", fontFamily: "inherit" }}
            >
              {researchFindings}
            </pre>
          ) : (
            <EmptyState msg="No research findings yet." />
          )}
        </div>
      )}
    </div>
  );
}

function CriticScoreBanner({ score }: { score: CriticScore }) {
  const pct = Math.round(score.overall * 100);
  const color =
    score.overall >= 0.8
      ? "#10b981"
      : score.overall >= 0.6
      ? "#f59e0b"
      : "#ef4444";

  return (
    <div
      className="rounded-2xl border p-4"
      style={{
        background: color + "10",
        borderColor: color + "40",
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border" style={{ borderColor: color + "40", color }}>
            QA
          </span>
          <span className="text-sm font-semibold" style={{ color }}>
            Critic Score: {pct}%
          </span>
        </div>
        <span
          className="text-xs px-2.5 py-1 rounded-full border font-medium"
          style={{
            color,
            borderColor: color + "60",
            background: color + "15",
          }}
        >
          {score.overall >= 0.8 ? "✓ Approved" : "Needs Review"}
        </span>
      </div>

      {/* Score bars */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        {[
          { label: "Engagement", val: score.engagement },
          { label: "Brand Align.", val: score.brand_alignment },
          { label: "Compliance", val: score.platform_compliance },
        ].map(({ label, val }) => (
          <div key={label}>
            <div
              className="flex justify-between mb-1"
              style={{ fontSize: 10, color: "var(--text-muted)" }}
            >
              <span>{label}</span>
              <span>{Math.round(val * 100)}%</span>
            </div>
            <div
              className="h-1.5 rounded-full overflow-hidden"
              style={{ background: "var(--border)" }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${val * 100}%`,
                  background: val >= 0.8 ? "#10b981" : val >= 0.6 ? "#f59e0b" : "#ef4444",
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {score.feedback && (
        <div
          className="text-xs leading-relaxed p-3 rounded-lg"
          style={{ background: "var(--surface-2)", color: "var(--text-muted)" }}
        >
          {score.feedback}
        </div>
      )}
    </div>
  );
}

function AdVariantCard({ variant }: { variant: AdVariant }) {
  const cfg = PLATFORM_CONFIG[variant.platform] ?? {
    label: variant.platform,
    icon: "DOC",
    color: "#2563eb",
    bg: "#eff6ff",
  };

  return (
    <div
      className="rounded-2xl border p-4 space-y-3 h-full"
      style={{ background: "var(--surface)", borderColor: cfg.color + "40" }}
    >
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border" style={{ borderColor: cfg.color + "40" }}>{cfg.icon}</span>
        <span className="text-xs font-semibold" style={{ color: cfg.color }}>
          {cfg.label}
        </span>
      </div>

      {variant.headline && (
        <div>
          <div
            className="text-xs uppercase tracking-wider mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Headline
          </div>
          <div className="text-sm font-semibold" style={{ color: "var(--text)" }}>
            {variant.headline}
          </div>
        </div>
      )}

      {variant.body && (
        <div>
          <div
            className="text-xs uppercase tracking-wider mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Body
          </div>
          <div
            className="text-xs leading-relaxed"
            style={{ color: "var(--text)" }}
          >
            {variant.body}
          </div>
        </div>
      )}

      {variant.cta && (
        <div
          className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium"
          style={{ background: cfg.color + "20", color: cfg.color }}
        >
          → {variant.cta}
        </div>
      )}

      {variant.image_prompt && (
        <div
          className="text-xs p-2 rounded-lg italic"
          style={{ background: "var(--surface-2)", color: "var(--text-muted)" }}
        >
          Image Prompt: {variant.image_prompt}
        </div>
      )}
    </div>
  );
}

function AudienceCard({ segment }: { segment: AudienceSegment }) {
  return (
    <div
      className="rounded-2xl border p-4"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="font-semibold text-sm mb-3" style={{ color: "var(--text)" }}>
        Segment: {segment.segment_name}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <TagGroup label="Seniority" tags={segment.seniority} color="#0284c7" />
        <TagGroup label="Industries" tags={segment.industries} color="#0891b2" />
        <TagGroup label="Geography" tags={segment.geo} color="#16a34a" />
        <TagGroup label="Interests" tags={segment.interests} color="#d97706" />
      </div>
    </div>
  );
}

function TagGroup({
  label,
  tags,
  color,
}: {
  label: string;
  tags: string[];
  color: string;
}) {
  if (!tags?.length) return null;
  return (
    <div>
      <div
        className="text-xs uppercase tracking-wider mb-1.5"
        style={{ color: "var(--text-muted)" }}
      >
        {label}
      </div>
      <div className="flex flex-wrap gap-1">
        {tags.slice(0, 4).map((t) => (
          <span
            key={t}
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: color + "20", color }}
          >
            {t}
          </span>
        ))}
        {tags.length > 4 && (
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: "var(--border)", color: "var(--text-muted)" }}
          >
            +{tags.length - 4}
          </span>
        )}
      </div>
    </div>
  );
}

function InfoCard({ title, content }: { title: string; content: string }) {
  return (
    <div
      className="rounded-xl border p-4"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="text-xs font-semibold uppercase tracking-wider mb-2"
        style={{ color: "var(--text-muted)" }}
      >
        {title}
      </div>
      <div className="text-sm" style={{ color: "var(--text)" }}>
        {content}
      </div>
    </div>
  );
}

function ListCard({
  title,
  items,
  color,
}: {
  title: string;
  items: string[];
  color: string;
}) {
  return (
    <div
      className="rounded-xl border p-4"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="text-xs font-semibold uppercase tracking-wider mb-2"
        style={{ color: "var(--text-muted)" }}
      >
        {title}
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2">
            <span
              className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0"
              style={{ background: color }}
            />
            <span className="text-xs" style={{ color: "var(--text)" }}>
              {item}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function EmptyState({ msg }: { msg: string }) {
  return (
    <div
      className="rounded-xl border p-8 text-center col-span-full"
      style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
    >
      <div className="text-sm">{msg}</div>
    </div>
  );
}
