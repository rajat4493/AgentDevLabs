import type { Trace } from "@/lib/types";

type TraceDetailProps = {
  trace: Trace | null;
  loading?: boolean;
};

export function TraceDetail({ trace, loading }: TraceDetailProps) {
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
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-900/60 bg-slate-900/50 p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <MetadataRow label="Trace ID" value={trace.id} mono />
          <MetadataRow
            label="Recorded"
            value={new Date(trace.created_at).toLocaleString()}
          />
          <MetadataRow label="Provider" value={trace.provider} />
          <MetadataRow label="Model" value={trace.model} mono />
          <MetadataRow label="Tokens" value={trace.tokens ?? "—"} />
          <MetadataRow label="Latency" value={trace.latency_ms ? `${trace.latency_ms} ms` : "—"} />
          <MetadataRow label="Framework" value={trace.framework || "—"} />
          <MetadataRow label="Source" value={trace.source || "—"} />
        </div>
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-900/60 bg-slate-950/60 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-widest text-slate-400">
            Prompt
          </h3>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-900/70 p-3 text-sm text-slate-200">
            {trace.input}
          </pre>
        </div>
        <div className="rounded-xl border border-slate-900/60 bg-slate-950/60 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-widest text-slate-400">
            Output
          </h3>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-900/70 p-3 text-sm text-slate-200">
            {trace.output || "—"}
          </pre>
        </div>
      </section>
      {trace.extra && (
        <section className="rounded-xl border border-slate-900/60 bg-slate-950/50 p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
            Extra Metadata
          </h3>
          <pre className="overflow-x-auto rounded-md bg-slate-900/80 p-3 text-xs text-slate-300">
            {JSON.stringify(trace.extra, null, 2)}
          </pre>
        </section>
      )}
    </div>
  );
}

type MetadataRowProps = {
  label: string;
  value: string | number;
  mono?: boolean;
};

function MetadataRow({ label, value, mono = false }: MetadataRowProps) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`text-sm font-semibold ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}
