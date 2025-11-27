"use client";

import { useEffect, useState } from "react";

export interface RoutingEfficiencyResponse {
  window_hours: number;
  efficiency_pct: number;
  delta_pct: number | null;
  total_runs: number;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL &&
  process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");

export function useRoutingEfficiency(windowHours: number = 168) {
  const [data, setData] = useState<RoutingEfficiencyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const params = new URLSearchParams({
          window_hours: String(windowHours),
        });
        const endpoint = API_BASE
          ? `${API_BASE}/v1/metrics/efficiency?${params.toString()}`
          : `/v1/metrics/efficiency?${params.toString()}`;
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setData(json);
        setError(null);
      } catch (err: any) {
        setError(err?.message || "Failed to load routing efficiency");
        setData(null);
      }
    }
    load();
  }, [windowHours]);

  return { data, error };
}
