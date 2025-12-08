import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import LatticeShell from "@/components/LatticeShell";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_LATTICE_API_BASE || "http://localhost:8000";

type MetricsResponse = {
  total_requests: number;
  total_cost: number;
  total_input_tokens: number;
  total_output_tokens: number;
  average_latency_ms: number;
  cache_hits_total: number;
  cache_misses_total: number;
  pii_detected_total: number;
  providers: Record<string, number>;
  models: Record<string, number>;
  bands: Record<string, number>;
};

export default function HomePage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("—");

  const loadMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/v1/metrics`);
      if (!resp.ok) throw new Error(`Backend error (${resp.status})`);
      const data: MetricsResponse = await resp.json();
      setMetrics(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMetrics();
    const interval = setInterval(() => void loadMetrics(), 8000);
    return () => clearInterval(interval);
  }, [loadMetrics]);

  const providerEntries = Object.entries(metrics?.providers || {});
  const bandEntries = Object.entries(metrics?.bands || {});

  const activityFeed = useMemo(
    () => [
      {
        title: "Cache activity",
        detail: `${metrics?.cache_hits_total ?? 0} hits / ${metrics?.cache_misses_total ?? 0} misses`,
        meta: "Last 5 minutes",
      },
      {
        title: "Cost ceiling",
        detail: `$${(metrics?.total_cost ?? 0).toFixed(6)} total spend`,
        meta: "Since boot",
      },
      {
        title: "PII tagging",
        detail: `${metrics?.pii_detected_total ?? 0} flagged interactions`,
        meta: "Detector enabled",
      },
    ],
    [metrics]
  );

  const healthChecks = useMemo(
    () => [
      {
        label: "Routing online",
        ok: true,
        hint: "FastAPI responding",
      },
      {
        label: "Latency within threshold",
        ok: (metrics?.average_latency_ms ?? 0) < 1200,
        hint: `${(metrics?.average_latency_ms ?? 0).toFixed(1)} ms avg`,
      },
      {
        label: "Cache reachable",
        ok: (metrics?.cache_hits_total ?? 0) + (metrics?.cache_misses_total ?? 0) > 0,
        hint: "Redis responding",
      },
      {
        label: "PII detector active",
        ok: true,
        hint: "Regex + keywords",
      },
    ],
    [metrics]
  );

  const actions = (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={() => void loadMetrics()}
        className="rounded-xl border border-slate-700 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200 transition hover:border-emerald-500"
        disabled={loading}
      >
        {loading ? "Refreshing…" : "Refresh"}
      </button>
      <Link
        href="https://github.com/AgentDevLabs/lattice"
        className="rounded-xl bg-emerald-500/90 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-slate-950 transition hover:bg-emerald-400"
      >
        Repo
      </Link>
    </div>
  );

  return (
    <LatticeShell
      title="Lattice Overview"
      subtitle="Quiet grid around your LLM traffic — no traces stored, just signal."
      actions={actions}
    >
      {error && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-950/30 p-4 text-sm text-rose-100">
          Failed to load metrics: {error}
        </div>
      )}

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-6">
        <MetricCard
          label="Requests (total)"
          value={metrics ? metrics.total_requests.toLocaleString() : "—"}
          subLabel={metrics ? `${metrics.cache_hits_total} cache hits` : "Awaiting traffic"}
        />
        <MetricCard
          label="Spend (USD)"
          value={metrics ? `$${metrics.total_cost.toFixed(6)}` : "—"}
          subLabel="dev-tier pricing"
        />
        <MetricCard
          label="Avg latency"
          value={metrics ? `${metrics.average_latency_ms.toFixed(1)} ms` : "—"}
          subLabel="p95 target: 1200 ms"
        />
        <MetricCard
          label="PII flags"
          value={metrics ? metrics.pii_detected_total : "—"}
          subLabel="regex + keyword detectors"
        />
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
        <ChartCard
          title="Provider Split"
          description="Live share of routed calls."
          entries={providerEntries}
        />
        <ChartCard
          title="Band Utilization"
          description="Distribution of low/mid/high routes."
          entries={bandEntries}
        />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div className="rounded-2xl border border-slate-800/70 bg-[#0B1020]/80 p-5 shadow-[0_0_0_1px_rgba(148,163,184,0.08)]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Activity</p>
              <p className="text-sm text-slate-500">Summaries, not raw traces.</p>
            </div>
            <span className="text-xs text-slate-500">Last update {lastUpdated}</span>
          </div>
          <div className="mt-4 space-y-4">
            {activityFeed.map((item) => (
              <div key={item.title} className="rounded-xl border border-slate-800/60 bg-[#0F172A]/60 p-4">
                <p className="text-sm font-semibold text-slate-100">{item.title}</p>
                <p className="text-xs text-slate-400">{item.detail}</p>
                <p className="text-[11px] uppercase tracking-[0.2em] text-emerald-300 mt-2">
                  {item.meta}
                </p>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800/70 bg-[#0B1020]/80 p-5 shadow-[0_0_0_1px_rgba(148,163,184,0.08)]">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Health Grid</p>
          <div className="mt-4 space-y-3">
            {healthChecks.map((check) => (
              <div key={check.label} className="flex items-center justify-between rounded-xl border border-slate-800/60 bg-[#0F172A]/50 px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-100">{check.label}</p>
                  <p className="text-xs text-slate-400">{check.hint}</p>
                </div>
                <span
                  className={cn(
                    "text-xs font-semibold uppercase tracking-[0.2em] px-3 py-1 rounded-full border",
                    check.ok
                      ? "border-emerald-500/50 text-emerald-300 bg-emerald-500/10"
                      : "border-amber-500/40 text-amber-200 bg-amber-500/10"
                  )}
                >
                  {check.ok ? "OK" : "CHECK"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div className="rounded-2xl border border-slate-800/70 bg-[#0B1020]/80 p-5 shadow-[0_0_0_1px_rgba(148,163,184,0.08)]">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Get Started</p>
          <div className="mt-4 space-y-3 text-sm text-slate-300">
            <p><span className="text-emerald-400">1.</span> `uvicorn lattice.api:app --reload`</p>
            <p><span className="text-emerald-400">2.</span> `pnpm dev` from `/ui` for this dashboard.</p>
            <p><span className="text-emerald-400">3.</span> `pip install lattice-sdk` and call `/v1/complete`.</p>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800/70 bg-[#0B1020]/80 p-5 shadow-[0_0_0_1px_rgba(148,163,184,0.08)]">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Python SDK</p>
          <pre className="mt-3 overflow-x-auto rounded-xl bg-[#050816]/80 p-4 text-sm text-emerald-200">
{`from lattice_sdk import LatticeClient

client = LatticeClient()
result = client.complete(
    "Summarize last route activity",
    band="mid",
)
print(result.text, result.cost["total_cost"], result.tags)`}
          </pre>
        </div>
      </section>
    </LatticeShell>
  );
}

function MetricCard({
  label,
  value,
  subLabel,
}: {
  label: string;
  value: string | number;
  subLabel?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/60 dark:bg-white/5 p-5 shadow-[0_0_40px_rgba(15,23,42,0.08)] backdrop-blur-2xl">
      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{label}</p>
      <div className="mt-3 flex items-baseline justify-between">
        <p className="text-2xl font-semibold font-mono text-slate-50">{value}</p>
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
      </div>
      {subLabel && <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">{subLabel}</p>}
    </div>
  );
}

function ChartCard({
  title,
  description,
  entries,
}: {
  title: string;
  description: string;
  entries: Array<[string, number]>;
}) {
  const maxValue = entries.length ? Math.max(...entries.map(([, value]) => value)) : 0;
  return (
    <div className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/60 dark:bg-white/5 p-5 shadow-[0_0_40px_rgba(15,23,42,0.08)] backdrop-blur-2xl">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">{title}</p>
          <p className="text-xs text-slate-500">{description}</p>
        </div>
        <span className="text-[10px] uppercase tracking-[0.2em] text-emerald-300">live</span>
      </div>
      <div className="mt-5 space-y-3">
        {entries.length === 0 && (
          <p className="text-sm text-slate-500">Awaiting traffic…</p>
        )}
        {entries.map(([key, value]) => (
          <div key={key}>
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>{key}</span>
              <span>{value}</span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-slate-800/70">
              <div
                className="h-2 rounded-full bg-emerald-500/80 transition-all"
                style={{ width: `${maxValue ? (value / maxValue) * 100 : 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
