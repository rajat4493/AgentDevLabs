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

type CostTrendProps = {
  windowHours: number;
  bucket: "hour" | "day";
};

export function CostTrendChart({ windowHours, bucket }: CostTrendProps) {
  const { data, loading, error } = useTimeseries(
    "cost",
    windowHours,
    bucket,
  );

  const chartData = data.map((point) => ({
    ...point,
    label: new Date(point.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <div className="flex h-64 flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-100">
          Cost Trends (last 24h)
        </h3>
        <p className="text-xs text-slate-500">
          Total LLM spend bucketed hourly.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400">
          Failed to load cost timeseries: {error}
        </p>
      )}

      {!loading && chartData.length === 0 && !error && (
        <p className="mt-4 text-xs text-slate-500">
          No cost data yet. Run some requests through the router.
        </p>
      )}

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#334155" strokeDasharray="3 3" opacity={0.2} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#334155",
                borderRadius: 8,
                fontSize: 11,
              }}
              labelStyle={{ color: "#e2e8f0" }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#38bdf8"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
