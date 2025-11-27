"use client";

import { useRoutingEfficiency } from "@/hooks/useRoutingEfficiency";

export function RoutingEfficiencyCard() {
  const { data, error } = useRoutingEfficiency(168);

  if (error || !data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-sm text-slate-400">
          Routing efficiency unavailable right now.
        </p>
      </div>
    );
  }

  const delta = data.delta_pct ?? 0;
  const hasDelta = data.delta_pct != null;
  const deltaPositive = delta >= 0;

  return (
    <div className="rounded-xl border border-indigo-500/40 bg-gradient-to-br from-[#0f172a] to-[#0a1020] p-6 text-slate-100">
      <h2 className="text-base font-semibold">Routing Efficiency</h2>
      <p className="text-3xl font-bold text-white">
        {data.efficiency_pct.toFixed(1)}%
      </p>
      {hasDelta && (
        <p
          className={`text-sm font-medium ${
            deltaPositive ? "text-emerald-400" : "text-rose-400"
          }`}
        >
          {deltaPositive ? "↑" : "↓"}
          {Math.abs(delta).toFixed(1)}% week-over-week
        </p>
      )}
      <p className="mt-2 text-xs text-slate-400">
        Based on {data.total_runs} runs over the last {data.window_hours / 24} days.
      </p>
    </div>
  );
}
