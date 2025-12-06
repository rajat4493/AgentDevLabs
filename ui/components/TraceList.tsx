import type { TraceListItem } from "@/lib/types";
import Link from "next/link";

type TraceListProps = {
  traces: TraceListItem[];
  loading?: boolean;
  onRefresh?: () => void;
};

const formatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "medium",
});

function formatLatency(latency?: number | null) {
  if (latency === null || latency === undefined) {
    return "—";
  }
  return `${latency} ms`;
}

export function TraceList({ traces, loading = false, onRefresh }: TraceListProps) {
  return (
    <div className="rounded-xl border border-slate-900/60 bg-slate-900/40">
      <div className="flex items-center justify-between border-b border-slate-900/60 px-4 py-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-amber-300">Recorded Traces</p>
          <p className="text-xs text-slate-400">Streaming directly from the RAJOS backend</p>
        </div>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-md border border-slate-800 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-200 transition hover:bg-slate-800/40 disabled:opacity-50"
            disabled={loading}
          >
            Refresh
          </button>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-900/70 text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Latency</th>
              <th className="px-4 py-3">Framework</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {traces.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-slate-500">
                  {loading ? "Loading traces..." : "No traces yet. Call the RAJOS SDK or router to generate one."}
                </td>
              </tr>
            )}
            {traces.map((trace) => (
              <tr
                key={trace.id}
                className="border-t border-slate-900/70 text-slate-200 transition hover:bg-slate-900/70"
              >
                <td className="px-4 py-3 text-xs font-mono">
                  {formatter.format(new Date(trace.created_at))}
                </td>
                <td className="px-4 py-3 capitalize">{trace.provider}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-300">{trace.model}</td>
                <td className="px-4 py-3">{formatLatency(trace.latency_ms)}</td>
                <td className="px-4 py-3">{trace.framework || "—"}</td>
                <td className="px-4 py-3">{trace.source || "—"}</td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/traces/${trace.id}`}
                    className="text-xs font-semibold uppercase tracking-widest text-amber-300 hover:text-amber-200"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
