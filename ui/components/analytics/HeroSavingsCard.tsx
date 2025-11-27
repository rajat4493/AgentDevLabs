"use client";

import { useEffect, useState } from "react";

interface SavingsResponse {
  actual_cost: number;
  baseline_cost: number;
  savings_usd: number;
  savings_pct: number;
  projected_monthly_savings: number;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL &&
  process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");

export function HeroSavingsCard() {
  const [data, setData] = useState<SavingsResponse | null>(null);

  useEffect(() => {
    const endpoint = API_BASE
      ? `${API_BASE}/v1/metrics/savings?window_hours=24`
      : "/v1/metrics/savings?window_hours=24";
    fetch(endpoint)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(setData)
      .catch(() => setData(null));
  }, []);

  if (!data) return null;

  return (
    <div className="rounded-xl border border-emerald-500/40 bg-gradient-to-br from-slate-900/60 to-slate-900/20 p-6 shadow-lg">
      <h2 className="text-base font-semibold text-white">Savings (Last 24h)</h2>
      <p className="text-2xl font-bold text-emerald-400">
        ${data.savings_usd.toFixed(5)}{" "}
        <span className="text-base font-semibold text-emerald-300">
          ({data.savings_pct.toFixed(1)}%)
        </span>
      </p>

      <div className="space-y-1 text-sm text-slate-400">
        <p>
          You spent{" "}
          <span className="text-slate-200">${data.actual_cost.toFixed(5)}</span>
        </p>
        <p>
          Baseline (all GPT-4o){" "}
          <span className="text-slate-200">
            ${data.baseline_cost.toFixed(5)}
          </span>
        </p>
      </div>

      <p className="pt-2 text-sm text-slate-500">
        Projected monthly savings:{" "}
        <span className="font-semibold text-emerald-300">
          ${data.projected_monthly_savings.toFixed(0)}
        </span>
      </p>
    </div>
  );
}
