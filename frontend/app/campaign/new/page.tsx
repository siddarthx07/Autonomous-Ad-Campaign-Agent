"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BACKEND_URL } from "@/lib/utils";

const GOALS = [
  "Brand Awareness",
  "Lead Generation",
  "Website Traffic",
  "Engagement",
  "Product Launch",
];

const CTA_OPTIONS = [
  "Book a Demo",
  "Start Free Trial",
  "Download Guide",
  "Get a Quote",
  "Join Waitlist",
  "Sign Up Free",
  "Request Access",
  "Learn More",
];

const TONES = ["Professional", "Bold", "Casual", "Inspirational", "Educational"];

const PLATFORMS = [
  { id: "linkedin", label: "LinkedIn" },
  { id: "twitter", label: "X / Twitter" },
];

const PUBLISH_MODES = [
  { id: "now",        label: "Publish Now",    desc: "All posts go live immediately" },
  { id: "scheduled",  label: "Schedule",        desc: "Space posts over time" },
  { id: "both",       label: "Now + Schedule",  desc: "First post live, rest scheduled" },
];

const CADENCES = [
  { id: "daily_1",  label: "Daily · 1 post",   desc: "One post every 24 hours" },
  { id: "daily_2",  label: "Daily · 2 posts",  desc: "Two posts per day, 12 h apart" },
  { id: "weekly",   label: "Weekly",            desc: "One post per week" },
  { id: "custom",   label: "Custom",            desc: "Define your own schedule" },
];

export default function NewCampaignPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    product_name: "",
    product_description: "",
    product_url: "",
    usp: "",
    cta_goal: "Book a Demo",
    cta_link: "",
    campaign_goal: "Lead Generation",
    target_audience: "",
    tone: "Professional",
    platforms: ["linkedin", "twitter"],
    publish_mode: "now",
    schedule_cadence: "daily_1",
    custom_cadence: "",
  });
  const [customCta, setCustomCta] = useState("");

  function togglePlatform(id: string) {
    setForm((f) => ({
      ...f,
      platforms: f.platforms.includes(id)
        ? f.platforms.filter((p) => p !== id)
        : [...f.platforms, id],
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const resp = await fetch(`${BACKEND_URL}/api/campaign/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || "Failed to start campaign");
      }

      const data = await resp.json();
      router.push(`/campaign/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1
          className="text-2xl font-bold mb-2 tracking-tight"
          style={{ color: "var(--text)" }}
        >
          New Campaign
        </h1>
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
          Describe your campaign brief. The agent will handle research, strategy,
          content creation, targeting, and publishing autonomously.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Product */}
        <FormSection title="Product">
          <Field label="Product / Brand Name" required>
            <input
              type="text"
              required
              placeholder="e.g. Acme CRM"
              value={form.product_name}
              onChange={(e) => setForm((f) => ({ ...f, product_name: e.target.value }))}
              className="input-field"
            />
          </Field>

          <Field label="Description" required>
            <textarea
              required
              rows={3}
              placeholder="What does your product do? Who is it for? What makes it unique?"
              value={form.product_description}
              onChange={(e) =>
                setForm((f) => ({ ...f, product_description: e.target.value }))
              }
              className="input-field resize-none"
            />
          </Field>

          <Field label="Landing Page URL">
            <input
              type="url"
              placeholder="https://yourproduct.com — researcher will pull real positioning from here"
              value={form.product_url}
              onChange={(e) => setForm((f) => ({ ...f, product_url: e.target.value }))}
              className="input-field"
            />
          </Field>

          <Field label="Unique Selling Proposition (USP)">
            <input
              type="text"
              placeholder="The one thing that makes you different — e.g. 10x faster onboarding with zero code"
              value={form.usp}
              onChange={(e) => setForm((f) => ({ ...f, usp: e.target.value }))}
              className="input-field"
            />
            <p className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>
              This anchors every headline and hook the content writer generates.
            </p>
          </Field>
        </FormSection>

        {/* Campaign Settings */}
        <FormSection title="Campaign Settings">
          <Field label="Goal">
            <div className="flex flex-wrap gap-2">
              {GOALS.map((g) => (
                <ChipButton
                  key={g}
                  active={form.campaign_goal === g}
                  onClick={() => setForm((f) => ({ ...f, campaign_goal: g }))}
                >
                  {g}
                </ChipButton>
              ))}
            </div>
          </Field>

          <Field label="Call-to-Action Goal">
            <div className="flex flex-wrap gap-2">
              {CTA_OPTIONS.map((c) => (
                <ChipButton
                  key={c}
                  active={form.cta_goal === c && !customCta}
                  onClick={() => {
                    setForm((f) => ({ ...f, cta_goal: c }));
                    setCustomCta("");
                  }}
                >
                  {c}
                </ChipButton>
              ))}
            </div>
            <input
              type="text"
              placeholder="Or type a custom CTA..."
              value={customCta}
              onChange={(e) => {
                setCustomCta(e.target.value);
                if (e.target.value)
                  setForm((f) => ({ ...f, cta_goal: e.target.value }));
              }}
              className="input-field mt-2"
            />
            <input
              type="url"
              placeholder="CTA Link — e.g. https://yourproduct.com/demo"
              value={form.cta_link}
              onChange={(e) => setForm((f) => ({ ...f, cta_link: e.target.value }))}
              className="input-field mt-2"
            />
            <p className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>
              This URL is embedded in the copy so readers know exactly where to go.
            </p>
          </Field>

          <Field label="Target Audience" required>
            <input
              type="text"
              required
              placeholder="e.g. B2B SaaS marketing directors at Series A-C startups"
              value={form.target_audience}
              onChange={(e) =>
                setForm((f) => ({ ...f, target_audience: e.target.value }))
              }
              className="input-field"
            />
          </Field>

          <Field label="Tone">
            <div className="flex flex-wrap gap-2">
              {TONES.map((t) => (
                <ChipButton
                  key={t}
                  active={form.tone === t}
                  onClick={() => setForm((f) => ({ ...f, tone: t }))}
                >
                  {t}
                </ChipButton>
              ))}
            </div>
          </Field>

          <Field label="Platforms">
            <div className="flex gap-3">
              {PLATFORMS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => togglePlatform(p.id)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all"
                  style={
                    form.platforms.includes(p.id)
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
                  {p.label}
                </button>
              ))}
            </div>
          </Field>
        </FormSection>

        {/* Publishing */}
        <FormSection title="Publishing">
          <Field label="When">
            <div className="grid grid-cols-3 gap-3">
              {PUBLISH_MODES.map((m) => {
                const active = form.publish_mode === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, publish_mode: m.id }))}
                    className="flex flex-col items-start gap-1 px-3 py-3.5 rounded-lg border text-left transition-all"
                    style={
                      active
                        ? {
                            background: "var(--accent-light)",
                            borderColor: "#bfdbfe",
                          }
                        : {
                            background: "transparent",
                            borderColor: "var(--border)",
                          }
                    }
                  >
                    <span
                      className="text-xs font-semibold"
                      style={{ color: active ? "var(--accent)" : "var(--text)" }}
                    >
                      {m.label}
                    </span>
                    <span
                      className="text-[11px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {m.desc}
                    </span>
                  </button>
                );
              })}
            </div>
          </Field>

          {form.publish_mode !== "now" && (
            <Field label="Posting Cadence">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {CADENCES.map((c) => {
                  const active = form.schedule_cadence === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() =>
                        setForm((f) => ({ ...f, schedule_cadence: c.id }))
                      }
                      className="flex flex-col items-start gap-0.5 px-3 py-3 rounded-lg border text-left transition-all"
                      style={
                        active
                          ? {
                              background: "#f0fdf4",
                              borderColor: "#bbf7d0",
                            }
                          : {
                              background: "transparent",
                              borderColor: "var(--border)",
                            }
                      }
                    >
                      <span
                        className="text-xs font-semibold"
                        style={{ color: active ? "var(--success)" : "var(--text)" }}
                      >
                        {c.label}
                      </span>
                      <span
                        className="text-[10px]"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {c.desc}
                      </span>
                    </button>
                  );
                })}
              </div>

              {form.schedule_cadence === "custom" && (
                <input
                  type="text"
                  placeholder="Describe your schedule — e.g. 3 posts on Mon / Wed / Fri"
                  value={form.custom_cadence}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, custom_cadence: e.target.value }))
                  }
                  className="input-field mt-3"
                />
              )}

              <p className="text-[11px] mt-2" style={{ color: "var(--text-muted)" }}>
                {form.schedule_cadence === "daily_1" &&
                  "Posts will be spaced 24 hours apart."}
                {form.schedule_cadence === "daily_2" &&
                  "Posts will be spaced 12 hours apart (2 per day)."}
                {form.schedule_cadence === "weekly" &&
                  "Posts will be spaced 7 days apart."}
                {form.schedule_cadence === "custom" &&
                  (form.custom_cadence || "Enter your custom schedule above.")}
              </p>
            </Field>
          )}
        </FormSection>

        {error && (
          <div
            className="rounded-lg border p-3 text-sm"
            style={{
              borderColor: "#fecaca",
              background: "var(--error-light)",
              color: "var(--error)",
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 rounded-lg font-semibold text-white text-sm transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: "var(--accent)",
            boxShadow: loading
              ? "none"
              : "0 1px 3px rgba(37,99,235,0.3), 0 4px 12px rgba(37,99,235,0.15)",
          }}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Launching Agents...
            </span>
          ) : (
            "Launch Campaign Agent"
          )}
        </button>
      </form>

      <style jsx>{`
        .input-field {
          width: 100%;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 10px 12px;
          color: var(--text);
          font-size: 14px;
          font-family: inherit;
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .input-field:focus {
          border-color: var(--accent);
          box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
        }
        .input-field::placeholder {
          color: var(--text-muted);
          opacity: 0.7;
        }
      `}</style>
    </div>
  );
}

function FormSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-xl border p-5 space-y-4"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <h2
        className="text-sm font-semibold"
        style={{ color: "var(--text)" }}
      >
        {title}
      </h2>
      {children}
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
        {label}
        {required && <span style={{ color: "var(--error)" }}> *</span>}
      </label>
      {children}
    </div>
  );
}

function ChipButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="px-3 py-1.5 rounded-md text-xs font-medium border transition-all"
      style={
        active
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
      {children}
    </button>
  );
}
