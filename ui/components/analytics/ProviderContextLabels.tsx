"use client";

import { useProviderMetrics } from "@/hooks/useProviders";

export function ProviderContextLabels() {
  const { data } = useProviderMetrics();

  return (
    <div className="mt-4 space-y-2">
      {data.map((provider) => {
        const high = provider.band_high_pct ?? 0;
        const medium = provider.band_medium_pct ?? 0;
        const low = provider.band_low_pct ?? 0;

        let message = "Mix of traffic bands";
        if (high > medium && high > low && high > 20) {
          message = "Mostly complex / high-band traffic";
        } else if (medium >= high && medium > low) {
          message = "Mostly medium-band tasks";
        } else if (low > medium && low > high) {
          message = "Mostly simple / low-band prompts";
        }

        return (
          <div key={provider.provider} className="text-sm text-slate-300">
            <span className="font-semibold text-white">{provider.provider}</span>
            <span className="text-slate-500"> — </span>
            <span>{message}</span>
          </div>
        );
      })}
    </div>
  );
}
