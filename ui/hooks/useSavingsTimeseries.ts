"use client";

import { useEffect, useState } from "react";

export interface SavingsPoint {
  timestamp: string;
  actual_cost: number;
  baseline_cost: number;
  savings_usd: number;
  cumulative_savings: number;
}

export interface SavingsTrendResponse {
  window_hours: number;
  bucket: string;
  points: SavingsPoint[];
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL &&
  process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");

let firstRunCache: string | null | undefined;

async function getFirstRunDate(): Promise<string | null> {
  if (firstRunCache !== undefined) {
    return firstRunCache ?? null;
  }
  try {
    const endpoint = API_BASE
      ? `${API_BASE}/v1/metrics/first_run`
      : "/v1/metrics/first_run";
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error("failed");
    const json = await res.json();
    firstRunCache = json?.first_run_at ?? null;
    return firstRunCache ?? null;
  } catch {
    firstRunCache = null;
    return null;
  }
}

export function useSavingsTimeseries(
  windowHours: number = 168,
  bucket: string = "day",
) {
  const [data, setData] = useState<SavingsPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          window_hours: String(windowHours),
          bucket,
        });
        const endpoint = API_BASE
          ? `${API_BASE}/v1/metrics/savings/timeseries?${params.toString()}`
          : `/v1/metrics/savings/timeseries?${params.toString()}`;
        const res = await fetch(endpoint);
        if (!res.ok) {
          if (res.status === 422) {
            const firstRun = await getFirstRunDate();
            if (firstRun) {
              const dateString = new Date(firstRun).toLocaleString();
              setError(`First data available starting ${dateString}.`);
            } else {
              setError("No savings data yet. Run traffic to populate this view.");
            }
            setData([]);
            return;
          }
          throw new Error(`HTTP ${res.status}`);
        }
        const json: SavingsTrendResponse = await res.json();
        setData(json.points || []);
      } catch (err: any) {
        setError(err?.message || "Failed to load savings trend.");
        setData([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [windowHours, bucket]);

  return { data, loading, error };
}
