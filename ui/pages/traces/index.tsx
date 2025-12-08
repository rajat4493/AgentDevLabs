import { useEffect, useState } from "react";
import LatticeShell from "@/components/LatticeShell";

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
  bands: Record<string, number>;
  models: Record<string, number>;
};

const API_BASE = process.env.NEXT_PUBLIC_LATTICE_API_BASE || "http://localhost:8000";

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/v1/metrics`);
      if (!resp.ok) throw new Error(`Backend error (${resp.status})`);
      const data: MetricsResponse = await resp.json();
      setMetrics(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(), 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <LatticeShell
      title="Metrics Monitor"
      subtitle="Lattice Dev Edition only exposes aggregated metrics—no per-trace storage."
      actions={
        <button
          type="button"
          onClick={load}
          className="rounded-xl border border-slate-700/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-200 transition hover:border-emerald-500"
        >
          Refresh
        </button>
      }
    >
      {loading && <div className="rounded-2xl border border-slate-800/70 bg-[#0B1020]/80 py-16 text-center text-slate-200">Loading metrics...</div>}
      {error && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-950/30 py-16 text-center text-rose-100">
          Failed to load metrics. {error}
        </div>
      )}
      {metrics && !loading && !error && (
        <div className="space-y-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Metric label="Total Requests" value={metrics.total_requests.toLocaleString()} />
            <Metric label="Total Cost (USD)" value={`$${metrics.total_cost.toFixed(6)}`} />
            <Metric label="Avg Latency (ms)" value={metrics.average_latency_ms.toFixed(1)} />
            <Metric label="Input Tokens" value={metrics.total_input_tokens.toLocaleString()} />
            <Metric label="Output Tokens" value={metrics.total_output_tokens.toLocaleString()} />
            <Metric label="PII/PHI Flags" value={metrics.pii_detected_total} />
            <Metric label="Cache Hits" value={metrics.cache_hits_total} />
            <Metric label="Cache Misses" value={metrics.cache_misses_total} />
          </div>

          <Breakdown title="Providers" entries={metrics.providers} />
          <Breakdown title="Bands" entries={metrics.bands} />
          <Breakdown title="Models" entries={metrics.models} mono />
        </div>
      )}
    </LatticeShell>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/60 dark:bg-white/5 p-5 text-center shadow-[0_0_40px_rgba(15,23,42,0.08)] backdrop-blur-2xl">
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-3 text-2xl font-semibold font-mono text-slate-800 dark:text-slate-50">{value}</p>
    </div>
  );
}

function Breakdown({
  title,
  entries,
  mono = false,
}: {
  title: string;
  entries: Record<string, number>;
  mono?: boolean;
}) {
  const keys = Object.keys(entries);
  if (keys.length === 0) {
    return null;
  }
  return (
    <div>
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{title}</h2>
      <table className="min-w-full divide-y divide-slate-900/50 rounded-2xl border border-slate-900/60 bg-[#0B1020]/70 text-sm text-slate-100">
        <thead className="bg-slate-900/60 text-left text-[11px] uppercase tracking-[0.2em] text-slate-400">
          <tr>
            <th className="px-4 py-2">{title.slice(0, -1)}</th>
            <th className="px-4 py-2">Count</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key} className="border-t border-slate-900/60">
              <td className={`px-4 py-2 ${mono ? "font-mono" : "capitalize"}`}>{key}</td>
              <td className="px-4 py-2">{entries[key]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
