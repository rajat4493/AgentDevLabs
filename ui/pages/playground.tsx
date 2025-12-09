import { FormEvent, useState } from "react";
import dynamic from "next/dynamic";
import LatticeShell from "@/components/LatticeShell";

const API_BASE = process.env.NEXT_PUBLIC_LATTICE_API_BASE || "http://localhost:8000";

type CompletionPayload = {
  text: string;
  provider: string;
  model: string;
  latency_ms?: number;
  cost?: Record<string, number>;
  tags?: string[];
  band?: string;
  routing_reason?: string;
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
  };
};

function PlaygroundPage() {
  const [prompt, setPrompt] = useState("");
  const [band, setBand] = useState("low");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [metadata, setMetadata] = useState("{}");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompletionPayload | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    let metadataPayload: Record<string, unknown> = {};
    if (metadata.trim()) {
      try {
        metadataPayload = JSON.parse(metadata);
      } catch (err) {
        setError("Metadata must be valid JSON.");
        setLoading(false);
        return;
      }
    }

    try {
      const resp = await fetch(`${API_BASE}/v1/complete`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          band: band || undefined,
          provider: provider || undefined,
          model: model || undefined,
          metadata: metadataPayload,
        }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        const message = data?.error?.message || "Request failed.";
        throw new Error(message);
      }

      const data = (await resp.json()) as CompletionPayload;
      setResult(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <LatticeShell
      title="Playground"
      subtitle="Send prompts through Lattice without storing raw content."
      actions={
        <button
          type="button"
          onClick={() => setPrompt("")}
          className="rounded-xl border border-slate-700/80 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-slate-200 transition hover:border-emerald-500"
        >
          Clear
        </button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={handleSubmit} className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/70 p-5 shadow-[0_0_40px_rgba(15,23,42,0.08)] dark:bg-white/5 backdrop-blur-2xl space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400 mb-2">
              Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              required
              className="w-full rounded-2xl border border-slate-200/80 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 px-3 py-3 text-sm text-slate-900 dark:text-slate-100 shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-400/50"
              rows={8}
              placeholder="Describe what you want Lattice to route…"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400 mb-2">
                Band
              </label>
              <select
                value={band}
                onChange={(event) => setBand(event.target.value)}
                className="w-full rounded-xl border border-slate-200/80 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
              >
                <option value="low">Low</option>
                <option value="mid">Mid</option>
                <option value="high">High</option>
              </select>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400 mb-2">
                Provider (optional)
              </label>
              <input
                value={provider}
                onChange={(event) => setProvider(event.target.value)}
                className="w-full rounded-xl border border-slate-200/80 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
                placeholder="openai, anthropic…"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400 mb-2">
                Model override
              </label>
              <input
                value={model}
                onChange={(event) => setModel(event.target.value)}
                className="w-full rounded-xl border border-slate-200/80 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
                placeholder="gpt-4o-mini"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400 mb-2">
                Metadata (JSON)
              </label>
              <textarea
                value={metadata}
                onChange={(event) => setMetadata(event.target.value)}
                className="w-full rounded-xl border border-slate-200/80 dark:border-slate-700 bg-white/80 dark:bg-slate-900/40 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
                rows={3}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-emerald-500/90 hover:bg-emerald-400 text-slate-900 font-semibold uppercase tracking-[0.3em] py-3 transition disabled:opacity-50"
          >
            {loading ? "Routing…" : "Route Prompt"}
          </button>
          {error && <p className="text-sm text-rose-400">{error}</p>}
        </form>

        <div className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/60 dark:bg-white/5 p-5 shadow-[0_0_40px_rgba(15,23,42,0.08)] backdrop-blur-2xl min-h-[400px]">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">Response</p>
          {!result && !error && !loading && (
            <p className="mt-6 text-sm text-slate-500 dark:text-slate-400">Submit a prompt to see the response here.</p>
          )}
          {result && (
            <div className="space-y-4 mt-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Output</p>
                <p className="mt-2 rounded-xl border border-slate-200/70 dark:border-slate-800/70 bg-white/70 dark:bg-slate-900/30 p-4 text-sm text-slate-900 dark:text-slate-100">
                  {result.text || "No text returned."}
                </p>
              </div>
              <div className="grid gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span>Provider: {result.provider}</span>
                <span>Model: {result.model}</span>
                <span>Latency: {result.latency_ms ?? 0} ms</span>
                <span>Cost: ${result.cost?.total_cost ?? 0}</span>
                <span>Band: {result.band || "—"}</span>
                <span>Tags: {result.tags?.join(", ") || "None"}</span>
              </div>
            </div>
          )}
          {loading && <p className="mt-6 text-sm text-slate-500 dark:text-slate-400">Routing prompt…</p>}
        </div>
      </div>
    </LatticeShell>
  );
}

export default dynamic(() => Promise.resolve(PlaygroundPage), {
  ssr: false,
});
