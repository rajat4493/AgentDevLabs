"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  LabelList,
} from "recharts";

import { useProviderMetrics } from "@/hooks/useProviders";

const COLORS = ["#38bdf8", "#a78bfa", "#f472b6", "#fbbf24", "#4ade80"];

function ProviderMixTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: any[];
}) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0];
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-100 shadow-lg">
      <p className="font-semibold capitalize">{item.name}</p>
      <p>{item.value.toFixed(2)}%</p>
    </div>
  );
}

export function ProviderMixChart() {
  const { data, loading, error } = useProviderMetrics();
  const totalRuns = data.reduce((sum, provider) => sum + provider.total_runs, 0);
  const chartData = data.map((provider) => ({
    name: provider.provider,
    value:
      totalRuns > 0 ? Number(((provider.total_runs / totalRuns) * 100).toFixed(2)) : 0,
  }));

  return (
    <div className="flex h-72 flex-col rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-slate-100">
          Traffic Distribution by Provider
        </h3>
        <p className="text-xs text-slate-500">
          Share of routed requests per provider.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400">Failed to load provider mix: {error}</p>
      )}
      {!loading && chartData.length === 0 && !error && (
        <p className="mt-4 text-xs text-slate-500">No traffic data yet.</p>
      )}

      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[index % COLORS.length]}
                  stroke="none"
                />
              ))}
              <LabelList
                dataKey="value"
                position="outside"
                formatter={(value: number) => `${value.toFixed(1)}%`}
                fill="#e2e8f0"
                stroke="none"
                fontSize={11}
              />
            </Pie>
            <Tooltip content={<ProviderMixTooltip />} />
            <Legend
              verticalAlign="bottom"
              wrapperStyle={{ color: "#cbd5f5", fontSize: 12 }}
              formatter={(value: string) => (
                <span className="text-slate-200">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
