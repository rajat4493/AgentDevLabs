"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE =
  process.env.NEXT_PUBLIC_AGENTICLABS_API ?? "http://localhost:8000";

type MetricsSummary = {
  total_runs: number;
  avg_latency_ms: number;
  total_cost_usd: number;
};

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE}/v1/metrics/summary`);

        if (!res.ok) {
          const text = await res.text();
          throw new Error(
            `Status ${res.status} ${res.statusText}: ${text || "<no body>"}`
          );
        }

        const data = (await res.json()) as MetricsSummary;
        setMetrics(data);
      } catch (err: any) {
        console.error("Failed to load metrics:", err);
        setError(err?.message ?? "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <main className="mx-auto max-w-5xl px-6 py-10 space-y-6">
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">
            Cost & Latency Overview
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Live snapshot from the AgenticLabs smart router.
          </p>
        </header>

        {loading && (
          <div className="text-sm text-slate-400">Loading metrics…</div>
        )}

        {error && !loading && (
          <Card className="border-red-500/40 bg-red-950/30">
            <CardHeader>
              <CardTitle className="text-red-200">
                Error loading metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-red-100 break-all">{error}</p>
              <p className="mt-2 text-xs text-red-200/70">
                Check that the API is running on{" "}
                <span className="font-mono">{API_BASE}</span> and that CORS
                allows this origin.
              </p>
            </CardContent>
          </Card>
        )}

        {!loading && !error && metrics && (
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm text-slate-300">
                  Total runs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold">
                  {metrics.total_runs ?? 0}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm text-slate-300">
                  Avg latency (ms)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold">
                  {metrics.avg_latency_ms?.toFixed(1) ?? "0.0"}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm text-slate-300">
                  Total cost (USD)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold">
                  {metrics.total_cost_usd?.toFixed(6) ?? "0.000000"}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  (Dummy for Ollama; will be real for OpenAI/Anthropic in P0)
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {!loading && !error && !metrics && (
          <p className="text-sm text-slate-400">
            No metrics yet. Trigger a run from the test form or via the API,
            then refresh this page.
          </p>
        )}
      </main>
    </div>
  );
}
