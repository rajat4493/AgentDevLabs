import { useCallback, useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import { TraceList } from "@/components/TraceList";
import type { TraceListItem } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_RAJOS_API_BASE || "http://localhost:8000";

type TraceListResponse = {
  items: TraceListItem[];
  total: number;
};

export default function TracesPage() {
  const [traces, setTraces] = useState<TraceListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTraces = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/traces?limit=50`);
      if (!resp.ok) throw new Error(`Backend error (${resp.status})`);
      const data: TraceListResponse = await resp.json();
      setTraces(data.items);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTraces();
  }, [loadTraces]);

  return (
    <Layout
      title="Trace Explorer"
      subtitle="Inspect every routed request from the last mile of your devkit."
      actions={
        <button
          type="button"
          onClick={loadTraces}
          className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-200 transition hover:border-amber-400"
        >
          Refresh
        </button>
      }
    >
      {error && (
        <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-950/40 p-3 text-sm text-rose-200">
          Failed to reach the RAJOS API: {error}
        </div>
      )}
      <TraceList traces={traces} loading={loading} onRefresh={loadTraces} />
    </Layout>
  );
}
