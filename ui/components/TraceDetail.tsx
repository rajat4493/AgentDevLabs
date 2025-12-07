import { useState } from "react";
import RoutingFlow from "@/components/RoutingFlow";
import type { Trace } from "@/lib/types";

type TraceDetailProps = {
  trace: Trace | null;
  loading?: boolean;
};

export function TraceDetail({ trace, loading }: TraceDetailProps) {
  const [extraOpen, setExtraOpen] = useState(false);
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-900/60 bg-slate-900/40 p-6 text-slate-400">
        Loading trace...
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-slate-500">
        Select a trace from the list to inspect inputs, outputs, and router metadata.
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-100">
      <section className="rounded-2xl border border-white/20 bg-white/10 p-5 shadow-xl shadow-black/30 backdrop-blur">
        <div className="mb-4">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-300">Trace</p>
          <p className="text-lg font-semibold text-white">#{trace.id}</p>
          <p className="text-sm text-slate-200">{new Date(trace.created_at).toLocaleString()}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Chip label="Provider" value={trace.provider} />
          <Chip label="Model" value={trace.model} />
          <Chip label="Latency" value={trace.latency_ms != null ? `${trace.latency_ms} ms` : "—"} />
          <Chip label="Tokens" value={trace.tokens != null ? trace.tokens : "—"} />
          <Chip label="Framework" value={trace.framework || "—"} />
          <Chip label="Source" value={trace.source || "—"} />
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              trace.status === "error"
                ? "bg-red-100/80 text-red-800"
                : "bg-green-100/80 text-green-800"
            }`}
          >
            {trace.status}
          </span>
        </div>
        {trace.error_message && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {trace.error_message}
          </div>
        )}
      </section>
      <div className="mt-6">
        <RoutingFlow provider={trace.provider} model={trace.model} source={trace.source || "router"} />
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-white/15 bg-white/5 p-4 shadow-lg shadow-black/30 backdrop-blur">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-200">Input</h3>
          <pre className="max-h-[400px] overflow-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-white/10 p-4 text-sm text-slate-100 backdrop-blur">
            {trace.input}
          </pre>
        </section>
        <section className="rounded-2xl border border-white/15 bg-white/5 p-4 shadow-lg shadow-black/30 backdrop-blur">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-200">Output</h3>
          <pre className="max-h-[400px] overflow-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-white/10 p-4 text-sm text-slate-100 backdrop-blur">
            {trace.output || "—"}
          </pre>
        </section>
      </div>
      <section className="rounded-2xl border border-white/15 bg-white/5 p-4 shadow-lg shadow-black/30 backdrop-blur">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-200">
            Extra Metadata
          </h3>
          {trace.extra && Object.keys(trace.extra).length > 0 && (
            <button
              type="button"
              onClick={() => setExtraOpen((prev) => !prev)}
              className="text-xs font-semibold uppercase tracking-wide text-amber-300 hover:text-amber-200"
            >
              {extraOpen ? "Hide" : "Show"}
            </button>
          )}
        </div>
        {trace.extra && Object.keys(trace.extra).length > 0 ? (
          extraOpen ? (
            <pre className="max-h-[400px] overflow-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-white/10 p-4 text-sm text-slate-100 backdrop-blur">
              {JSON.stringify(trace.extra, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-slate-300">Metadata hidden.</p>
          )
        ) : (
          <p className="text-sm text-slate-400">No additional metadata.</p>
        )}
      </section>
    </div>
  );
}

type ChipProps = { label: string; value: string | number };

function Chip({ label, value }: ChipProps) {
  return (
    <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white shadow-inner shadow-black/40 backdrop-blur">
      {label}: {value}
    </span>
  );
}
