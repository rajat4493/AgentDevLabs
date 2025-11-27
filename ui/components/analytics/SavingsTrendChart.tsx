"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useSavingsTimeseries } from "@/hooks/useSavingsTimeseries";

export function SavingsTrendChart() {
  const { data, loading, error } = useSavingsTimeseries(168, "day");
  const chartData = data.map((point) => ({
    label: new Date(point.timestamp).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    }),
    savings: Number(point.savings_usd.toFixed(6)),
    cumulative: Number(point.cumulative_savings.toFixed(6)),
  }));

  return (
    <div className="flex h-72 flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-100">
          Savings Trend (Daily)
        </h3>
        <p className="text-xs text-slate-500">
          Daily savings vs baseline with cumulative growth.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400">Failed to load savings trend: {error}</p>
      )}
      {!loading && chartData.length === 0 && !error && (
        <p className="mt-4 text-xs text-slate-500">
          No savings data yet. Run more traffic to populate this chart.
        </p>
      )}

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
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
            <Bar
              yAxisId="left"
              dataKey="savings"
              fill="#22d3ee"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cumulative"
              stroke="#f97316"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
