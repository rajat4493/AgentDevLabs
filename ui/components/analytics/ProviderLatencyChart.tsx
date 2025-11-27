"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useProviderMetrics } from "@/hooks/useProviders";

export function ProviderLatencyChart() {
  const { data, loading, error } = useProviderMetrics();

  const chartData = data.map((provider) => ({
    provider: provider.provider,
    latency: Number(provider.avg_latency_ms?.toFixed(2) ?? 0),
  }));

  return (
    <div className="flex h-72 flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-100">
          Avg Latency by Provider
        </h3>
        <p className="text-xs text-slate-500">
          Compare responsiveness across your LLM vendors.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400">Failed to load latency data: {error}</p>
      )}

      {!loading && chartData.length === 0 && !error && (
        <p className="mt-4 text-xs text-slate-500">No latency data yet.</p>
      )}

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
            <XAxis
              dataKey="provider"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              unit="ms"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                borderColor: "#334155",
                borderRadius: 8,
                fontSize: 11,
              }}
              labelStyle={{ color: "#e2e8f0" }}
            />
            <Bar dataKey="latency" fill="#f472b6" radius={4} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
