import Link from "next/link";
import { Layout } from "@/components/Layout";

const features = [
  {
    title: "Trace Everything",
    description: "Persist every LLM call locally with inputs, outputs, latency, and arbitrary metadata.",
  },
  {
    title: "Route Intelligently",
    description: "Use the built-in FastAPI router to select providers/models with the same logic as production.",
  },
  {
    title: "Instrument via SDK",
    description: "Drop the rajos Python decorator or client into any stack to publish traces instantly.",
  },
];

const steps = [
  "Start the FastAPI backend: `uvicorn backend.main:app --reload`",
  "Run the Next.js dashboard: `pnpm dev` (from /ui)",
  "Install the SDK locally: `pip install -e ./sdk-python` and wrap your LLM calls",
];

export default function HomePage() {
  return (
    <Layout
      title="RAJOS · the LLM tracing & routing devkit"
      subtitle="A local-first toolkit for understanding, debugging, and steering every model call."
      actions={
        <div className="flex gap-3">
          <Link
            href="/traces"
            className="rounded-lg bg-amber-400 px-5 py-2 text-sm font-semibold uppercase tracking-[0.3em] text-slate-950 transition hover:bg-amber-300"
          >
            View Traces
          </Link>
          <a
            href="https://github.com/AgentDevLabs/RAJOS"
            className="rounded-lg border border-slate-700 px-5 py-2 text-sm font-semibold uppercase tracking-[0.3em] text-slate-100 transition hover:border-slate-500"
          >
            Repo
          </a>
        </div>
      }
    >
      <section className="grid gap-6 lg:grid-cols-3">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="rounded-2xl border border-slate-900/60 bg-slate-900/40 p-5 shadow-2xl shadow-amber-500/5"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-400">Feature</p>
            <h3 className="mt-2 text-lg font-semibold text-white">{feature.title}</h3>
            <p className="mt-1 text-sm text-slate-400">{feature.description}</p>
          </div>
        ))}
      </section>

      <section className="mt-10 rounded-2xl border border-slate-900/60 bg-slate-950/60 p-6">
        <h2 className="text-xl font-semibold text-white">Get started locally</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-300">
          {steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>

      <section className="mt-10 rounded-2xl border border-slate-900/60 bg-slate-900/30 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-400">Python SDK</p>
        <h2 className="text-xl font-semibold">Trace an LLM call in two lines</h2>
        <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-950/80 p-4 text-sm text-amber-100">
{`from rajos import trace_llm_call

@trace_llm_call(provider="openai", model="gpt-4o-mini")
def ask_llm(prompt: str) -> str:
    return openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])`}
        </pre>
      </section>
    </Layout>
  );
}
