# Lattice Dev Edition Roadmap

## Near-term

- **PII tag tuning.** Expand regex + keyword coverage and add severity levels while keeping the no-storage guarantee.
- **Metrics sinks.** Optional Redis/influx counters so aggregates survive server restarts without per-request logs.
- **Provider overrides.** Expose `provider_overrides` in `bands.json` + `/v1/complete` payload.
- **Inline eval hooks.** Allow lightweight callouts (e.g., toxicity classifiers) that only emit tags, not raw text.

## Mid-term

- **TypeScript client.** Match the Python SDK with a small `lattice-sdk` package for Node scripts + Vercel functions.
- **CLI scaffolding.** `lattice dev` helper that boots Redis + uvicorn + sample prompts from a single command.
- **Workspace cache.** Optional in-memory cache backend for teams without Redis.

## Long-term

- **Aggregated export.** Nightly CSV or Parquet dumps with metrics per provider/band instead of trace rows.
- **Custom bands.** Plug in new scorers and configs through entrypoints.
- **Cost guardrails.** User-defined budget thresholds that short-circuit routes before they leave the box.
