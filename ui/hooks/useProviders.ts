"use client";

import { useEffect, useState } from "react";

export interface ProviderMetrics {
  provider: string;
  total_runs: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  high_risk_pct?: number;
  band_low_pct?: number;
  band_medium_pct?: number;
  band_high_pct?: number;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL &&
  process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");

export function useProviderMetrics() {
  const [data, setData] = useState<ProviderMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);

      try {
        const endpoint = API_BASE
          ? `${API_BASE}/v1/metrics/providers`
          : "/v1/metrics/providers";
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setData(json.items || json.providers || json || []);
      } catch (err: any) {
        setError(err?.message || "Failed to load provider metrics");
        setData([]);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return { data, loading, error };
}
