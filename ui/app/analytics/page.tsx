"use client";

import { useState } from "react";

import { CostTrendChart } from "@/components/analytics/CostTrendChart";
import { AlriTrendChart } from "@/components/analytics/AlriTrendChart";
import { ProviderCostChart } from "@/components/analytics/ProviderCostChart";
import { ProviderLatencyChart } from "@/components/analytics/ProviderLatencyChart";
import { ProviderRiskChart } from "@/components/analytics/ProviderRiskChart";
import { HeroSavingsCard } from "@/components/analytics/HeroSavingsCard";
import { ProviderContextLabels } from "@/components/analytics/ProviderContextLabels";
import { SavingsTrendChart } from "@/components/analytics/SavingsTrendChart";
import { RoutingEfficiencyCard } from "@/components/analytics/RoutingEfficiencyCard";
import { ProviderMixChart } from "@/components/analytics/ProviderMixChart";
import { CategoryDistributionChart } from "@/components/analytics/CategoryDistributionChart";

const WINDOW_PRESETS = [
  { id: "24h", label: "Last 24 Hours", hours: 24, bucket: "hour" as const },
  { id: "5d", label: "Last 5 Days", hours: 24 * 5, bucket: "day" as const },
  { id: "7d", label: "Last 7 Days", hours: 24 * 7, bucket: "day" as const },
  { id: "30d", label: "Last 30 Days", hours: 24 * 30, bucket: "day" as const },
  { id: "90d", label: "Last Quarter", hours: 24 * 90, bucket: "day" as const },
  { id: "365d", label: "Last Year", hours: 24 * 365, bucket: "day" as const },
  { id: "custom", label: "Custom (hours)", hours: 24 * 7, bucket: "day" as const },
] as const;

function formatWindowLabel(hours: number) {
  if (hours < 24) return `${hours} hours`;
  const days = hours / 24;
  if (days < 30) return `${Number(days.toFixed(days % 1 === 0 ? 0 : 1))} days`;
  const months = days / 30;
  if (months < 12) return `${Number(months.toFixed(1))} months`;
  const years = months / 12;
  return `${Number(years.toFixed(1))} years`;
}

export default function AnalyticsPage() {
  const [windowPresetId, setWindowPresetId] = useState("24h");
  const [customHours, setCustomHours] = useState(24 * 7);

  const preset =
    WINDOW_PRESETS.find((item) => item.id === windowPresetId) ??
    WINDOW_PRESETS[0];
  const effectiveHours =
    preset.id === "custom" ? Math.max(1, customHours || 1) : preset.hours;
  const bucket =
    preset.id === "custom"
      ? effectiveHours <= 72
        ? "hour"
        : "day"
      : preset.bucket;
  const windowLabel =
    preset.id === "custom" ? formatWindowLabel(effectiveHours) : preset.label;

  return (
    <main className="min-h-screen w-full space-y-10 px-8 py-6">
      <section className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="mt-1 text-sm text-slate-400">
            Deeper cost and performance insights for your router.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-200">
          <label className="text-xs uppercase tracking-wide text-slate-500">
            Reporting window
          </label>
          <select
            value={windowPresetId}
            onChange={(e) => setWindowPresetId(e.target.value)}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-400"
          >
            {WINDOW_PRESETS.map((preset) => (
              <option key={preset.id} value={preset.id}>
                {preset.label}
              </option>
            ))}
          </select>
          {windowPresetId === "custom" && (
            <input
              type="number"
              min={1}
              value={customHours}
              onChange={(e) =>
                setCustomHours(
                  Number.isNaN(Number(e.target.value))
                    ? 1
                    : Number(e.target.value),
                )
              }
              className="w-28 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          )}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <HeroSavingsCard windowHours={effectiveHours} label={windowLabel} />
          <RoutingEfficiencyCard windowHours={effectiveHours} label={windowLabel} />
        </div>
        <div className="lg:col-span-2">
          <SavingsTrendChart windowHours={effectiveHours} bucket={bucket} />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <CostTrendChart windowHours={effectiveHours} bucket={bucket} />
        <AlriTrendChart windowHours={effectiveHours} bucket={bucket} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <ProviderCostChart windowHours={effectiveHours} />
        <ProviderLatencyChart windowHours={effectiveHours} />
      </section>
      <ProviderContextLabels windowHours={effectiveHours} />

      <section className="grid gap-6 lg:grid-cols-2">
        <ProviderMixChart windowHours={effectiveHours} />
        <CategoryDistributionChart
          windowHours={effectiveHours}
          label={windowLabel}
        />
      </section>

      <section>
        <ProviderRiskChart windowHours={effectiveHours} />
      </section>

      <section>
        <p className="text-xs text-slate-500">
          Window applied to all charts above: {windowLabel}.
        </p>
      </section>
    </main>
  );
}
