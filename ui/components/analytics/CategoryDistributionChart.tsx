"use client";

import { useEffect, useState } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface CategoryPoint {
  category: string;
  runs: number;
  pct: number;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL &&
  process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");

export function CategoryDistributionChart() {
  const [data, setData] = useState<CategoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ window_hours: "168" });
        const endpoint = API_BASE
          ? `${API_BASE}/v1/metrics/categories?${params.toString()}`
          : `/v1/metrics/categories?${params.toString()}`;
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setData(json?.items ?? []);
      } catch (e: any) {
        setError(e?.message || "Failed to load category distribution");
        setData([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="flex h-72 flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-100">
          Query Category Distribution (7d)
        </h3>
        <p className="text-xs text-slate-500">
          Mix of workloads routed through the system.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400">Failed to load categories: {error}</p>
      )}
      {!loading && !error && data.length === 0 && (
        <p className="mt-4 text-xs text-slate-500">
          No category data yet. Run more traffic.
        </p>
      )}

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
            <XAxis
              dataKey="category"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              unit="%"
            />
            <Tooltip
              formatter={(value: number) => `${value.toFixed(1)}%`}
              contentStyle={{
                backgroundColor: "#020617",
                borderColor: "#334155",
                borderRadius: 8,
                fontSize: 11,
              }}
              labelStyle={{ color: "#e2e8f0" }}
            />
            <Bar dataKey="pct" fill="#60a5fa" radius={4} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
