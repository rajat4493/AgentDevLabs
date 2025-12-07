import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";

type StatsResponse = {
  total_traces: number;
  avg_latency_ms: number | null;
  avg_tokens: number | null;
  provider_counts: Record<string, number>;
  model_counts: Record<string, number>;
  daily_counts: { date: string; count: number }[];
};

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function StatsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (!res.ok) throw new Error("Backend error");
        const data: StatsResponse = await res.json();
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
    <Layout title="Stats" subtitle="Aggregated view of RAJOS activity.">
      {loading && <p className="text-center text-slate-400">Loading stats...</p>}
      {error && (
        <p className="text-center text-rose-300">Failed to load stats.</p>
      )}
      {stats && !loading && !error && (
        <div className="space-y-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Metric label="Total Traces" value={stats.total_traces} />
            <Metric
              label="Average Latency (ms)"
              value={stats.avg_latency_ms ? stats.avg_latency_ms.toFixed(1) : "—"}
            />
            <Metric
              label="Average Tokens"
              value={stats.avg_tokens ? stats.avg_tokens.toFixed(1) : "—"}
            />
            <Metric
              label="Providers Used"
              value={Object.keys(stats.provider_counts).length}
            />
            <Metric
              label="Models Used"
              value={Object.keys(stats.model_counts).length}
            />
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Providers
            </h2>
            <table className="min-w-full divide-y divide-slate-800 rounded-lg border border-slate-800 bg-white/5 text-sm text-slate-100">
              <thead className="bg-slate-900/40 text-left">
                <tr>
                  <th className="px-4 py-2">Provider</th>
                  <th className="px-4 py-2">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.provider_counts).map(([provider, count]) => (
                  <tr key={provider} className="border-t border-slate-800/70">
                    <td className="px-4 py-2 capitalize">{provider}</td>
                    <td className="px-4 py-2">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Models
            </h2>
            <table className="min-w-full divide-y divide-slate-800 rounded-lg border border-slate-800 bg-white/5 text-sm text-slate-100">
              <thead className="bg-slate-900/40 text-left">
                <tr>
                  <th className="px-4 py-2">Model</th>
                  <th className="px-4 py-2">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.model_counts).map(([model, count]) => (
                  <tr key={model} className="border-t border-slate-800/70">
                    <td className="px-4 py-2 font-mono">{model}</td>
                    <td className="px-4 py-2">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Layout>
  );
}

type MetricProps = { label: string; value: number | string };

function Metric({ label, value }: MetricProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-white/10 p-4 shadow-sm backdrop-blur">
      <h3 className="text-sm font-semibold text-slate-300">{label}</h3>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
