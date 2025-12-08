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
  models: Record<string, number>;
  bands: Record<string, number>;
};

const API_BASE = process.env.NEXT_PUBLIC_LATTICE_API_BASE || "http://localhost:8000";

export default function StatsPage() {
  const [stats, setStats] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/v1/metrics`);
        if (!res.ok) throw new Error("Backend error");
        const data: MetricsResponse = await res.json();
        setStats(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }

    void loadStats();
  }, []);

  return (
    <LatticeShell title="Stats" subtitle="Aggregated view of Lattice activity.">
      {loading && (
        <div className="rounded-2xl border border-slate-800/70 bg-[#0B1020]/70 p-6 text-center text-slate-300">
          Loading stats…
        </div>
      )}
      {error && (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-4 text-center text-rose-100">
          Failed to load stats. {error}
        </div>
      )}
      {stats && !loading && !error && (
        <div className="space-y-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Metric label="Total Requests" value={stats.total_requests} />
            <Metric
              label="Average Latency (ms)"
              value={stats.average_latency_ms ? stats.average_latency_ms.toFixed(1) : "—"}
            />
            <Metric
              label="Total Input Tokens"
              value={stats.total_input_tokens.toLocaleString()}
            />
            <Metric
              label="Total Output Tokens"
              value={stats.total_output_tokens.toLocaleString()}
            />
            <Metric
              label="Total Cost (USD)"
              value={`$${stats.total_cost.toFixed(6)}`}
            />
            <Metric
              label="PII/PHI Flags"
              value={stats.pii_detected_total}
            />
            <Metric
              label="Cache Hits / Misses"
              value={`${stats.cache_hits_total} / ${stats.cache_misses_total}`}
            />
          </div>

          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
              Providers
            </h2>
            <table className="min-w-full divide-y divide-slate-800/60 rounded-2xl border border-slate-800/70 bg-[#0B1020]/70 text-sm text-slate-100">
              <thead className="bg-slate-900/40 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-2">Provider</th>
                  <th className="px-4 py-2">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.providers).map(([provider, count]) => (
                  <tr key={provider} className="border-t border-slate-800/60">
                    <td className="px-4 py-2 capitalize">{provider}</td>
                    <td className="px-4 py-2">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
              Models
            </h2>
            <table className="min-w-full divide-y divide-slate-800/60 rounded-2xl border border-slate-800/70 bg-[#0B1020]/70 text-sm text-slate-100">
              <thead className="bg-slate-900/40 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-2">Model</th>
                  <th className="px-4 py-2">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.models).map(([model, count]) => (
                  <tr key={model} className="border-t border-slate-800/60">
                    <td className="px-4 py-2 font-mono text-xs">{model}</td>
                    <td className="px-4 py-2">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
              Bands
            </h2>
            <table className="min-w-full divide-y divide-slate-800/60 rounded-2xl border border-slate-800/70 bg-[#0B1020]/70 text-sm text-slate-100">
              <thead className="bg-slate-900/40 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-2">Band</th>
                  <th className="px-4 py-2">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.bands).map(([band, count]) => (
                  <tr key={band} className="border-t border-slate-800/60">
                    <td className="px-4 py-2 capitalize">{band}</td>
                    <td className="px-4 py-2">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </LatticeShell>
  );
}

type MetricProps = { label: string; value: number | string };

function Metric({ label, value }: MetricProps) {
  return (
    <div className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/60 dark:bg-white/5 p-5 shadow-[0_0_40px_rgba(15,23,42,0.08)] backdrop-blur-2xl">
      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold font-mono text-slate-800 dark:text-slate-50">{value}</p>
    </div>
  );
}
