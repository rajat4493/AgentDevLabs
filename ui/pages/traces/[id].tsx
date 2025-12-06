import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { Layout } from "@/components/Layout";
import { TraceDetail } from "@/components/TraceDetail";
import type { Trace } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_RAJOS_API_BASE || "http://localhost:8000";

export default function TraceDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [trace, setTrace] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!router.isReady || typeof id !== "string") {
      return;
    }
    setLoading(true);
    setTrace(null);
    setError(null);
    fetch(`${API_BASE}/api/traces/${id}`)
      .then(async (resp) => {
        if (!resp.ok) throw new Error(`Backend error (${resp.status})`);
        const data: Trace = await resp.json();
        setTrace(data);
      })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false));
  }, [router.isReady, id]);

  return (
    <Layout title="Trace Detail" subtitle={typeof id === "string" ? `Trace ${id}` : "Loading..."}>
      {error && (
        <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-950/40 p-3 text-sm text-rose-200">
          Failed to reach the RAJOS API: {error}
        </div>
      )}
      <TraceDetail trace={trace} loading={loading} />
    </Layout>
  );
}
