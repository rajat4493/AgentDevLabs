# RAJOS Roadmap

## Near-term

- **Trace filters & search** – date range, provider/model filters, and free-text search in the FastAPI `/api/traces` endpoint + UI.
- **SDK telemetry** – automatic token estimation + structured error reporting in the Python decorator.
- **Router profiling** – add cost + latency deltas per provider/model to the `/api/chat` response and trace metadata.
- **Desktop-friendly packaging** – templated scripts for booting backend + UI together (`make dev`, `just dev`).

## Mid-term

- **Multi-language SDKs** – TypeScript and Go clients with matching decorators/middleware.
- **Timeline visualizations** – render multi-step agent traces with spans + child events.
- **Provider sandbox runners** – optional local wrappers for Ollama and LiteLLM so you can test without cloud keys.

## Long-term

- **Sync adapters** – opt-in push to ClickHouse/Postgres/Snowflake for teams that outgrow SQLite.
- **Policy hooks** – lightweight guardrails (PII detection, prompt classifiers) that run before/after routing.
- **Plugin slots** – register custom adapters, band scorers, or trace enrichers via entrypoints.
