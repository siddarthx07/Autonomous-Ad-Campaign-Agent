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

const TONES = ["Professional", "Bold", "Casual", "Inspirational", "Educational"];

const PLATFORMS = [
  { id: "linkedin", label: "LinkedIn", icon: "💼" },
  { id: "buffer", label: "Buffer", icon: "📅" },
];

export default function NewCampaignPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    product_name: "",
    product_description: "",
    campaign_goal: "Lead Generation",
    target_audience: "",
    tone: "Professional",
    budget: "$500/week",
    platforms: ["linkedin", "buffer"],
  });

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
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text)" }}>
          New Campaign
        </h1>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Describe your campaign brief. The agent will handle research, strategy,
          content creation, targeting, and publishing autonomously.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Product */}
        <div
          className="rounded-2xl border p-5 space-y-4"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <h2 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
            Product
          </h2>

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
        </div>

        {/* Campaign */}
        <div
          className="rounded-2xl border p-5 space-y-4"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <h2 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
            Campaign Settings
          </h2>

          <Field label="Goal">
            <div className="flex flex-wrap gap-2">
              {GOALS.map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, campaign_goal: g }))}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
                  style={
                    form.campaign_goal === g
                      ? {
                          background: "rgba(99,102,241,0.2)",
                          borderColor: "#6366f1",
                          color: "#a5b4fc",
                        }
                      : {
                          background: "transparent",
                          borderColor: "var(--border)",
                          color: "var(--text-muted)",
                        }
                  }
                >
                  {g}
                </button>
              ))}
            </div>
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

          <div className="grid grid-cols-2 gap-4">
            <Field label="Tone">
              <select
                value={form.tone}
                onChange={(e) => setForm((f) => ({ ...f, tone: e.target.value }))}
                className="input-field"
              >
                {TONES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Budget">
              <input
                type="text"
                placeholder="e.g. $500/week"
                value={form.budget}
                onChange={(e) => setForm((f) => ({ ...f, budget: e.target.value }))}
                className="input-field"
              />
            </Field>
          </div>

          <Field label="Platforms">
            <div className="flex gap-3">
              {PLATFORMS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => togglePlatform(p.id)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-medium transition-all"
                  style={
                    form.platforms.includes(p.id)
                      ? {
                          background: "rgba(99,102,241,0.2)",
                          borderColor: "#6366f1",
                          color: "#a5b4fc",
                        }
                      : {
                          background: "transparent",
                          borderColor: "var(--border)",
                          color: "var(--text-muted)",
                        }
                  }
                >
                  <span>{p.icon}</span>
                  {p.label}
                </button>
              ))}
            </div>
          </Field>
        </div>

        {error && (
          <div
            className="rounded-xl border p-3 text-sm"
            style={{
              borderColor: "var(--error)",
              background: "rgba(239,68,68,0.1)",
              color: "var(--error)",
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 rounded-xl font-semibold text-white text-sm transition-all hover:scale-[1.01] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
          style={{
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            boxShadow: loading ? "none" : "0 0 30px rgba(99,102,241,0.4)",
          }}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Launching Agents...
            </span>
          ) : (
            "Launch Campaign Agent 🚀"
          )}
        </button>
      </form>

      <style jsx>{`
        .input-field {
          width: 100%;
          background: var(--surface-2);
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 10px 12px;
          color: var(--text);
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s;
        }
        .input-field:focus {
          border-color: var(--accent);
        }
        .input-field::placeholder {
          color: var(--text-muted);
        }
        select.input-field option {
          background: var(--surface-2);
        }
      `}</style>
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
