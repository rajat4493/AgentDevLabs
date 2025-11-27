"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useTimeseries } from "@/hooks/useTimeseries";

export function AlriTrendChart() {
  const { data, loading, error } = useTimeseries("alri", 24, "hour");

  const chartData = data.map((point) => ({
    ...point,
    label: new Date(point.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <div className="flex h-64 flex-col rounded-xl border border-indigo-800/70 bg-slate-900/40 p-4">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-100">
          ALRI Trends (last 24h)
        </h3>
        <p className="text-xs text-slate-500">
          Average ALRI score bucketed hourly for recent runs.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400">
          Failed to load ALRI timeseries: {error}
        </p>
      )}

      {!loading && chartData.length === 0 && !error && (
        <p className="mt-4 text-xs text-slate-500">
          No ALRI data in this window. Run a few requests to populate it.
        </p>
      )}

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#4c1d95" strokeDasharray="3 3" opacity={0.2} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: "#c4b5fd" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "#c4b5fd" }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#4c1d95",
                borderRadius: 8,
                fontSize: 11,
              }}
              labelStyle={{ color: "#e0e7ff" }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
