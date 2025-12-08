# Changelog

## [0.3.0] - 2024-XX-XX

- Rebranded RAJOS into **Lattice v0.3 – Dev Edition** with a new FastAPI surface at `lattice.api:app`.
- Implemented `/v1/complete`, `/v1/metrics`, `/v1/health`, and `/dashboard` while removing trace storage, SQL tables, and enterprise tenanting.
- Added regex-based PII/PHI tagging plus an aggregated, in-memory metrics collector that only tracks counters.
- Reused the routing, cost, and cache layers with hashed cache keys + short TTLs to avoid prompt retention.
- Shipped the new `lattice_sdk` Python client (with a `rajos` shim) exposing `LatticeClient.complete()`.

## [0.1.0] - 2024-12-07

- Pivoted the repo into the lattice developer-first toolkit with a clean `backend/`, `ui/`, and `sdk-python/` layout.
- Reused the existing routing logic + provider adapters inside a new FastAPI app that stores traces locally in SQLite.
- Added `/api/traces` CRUD endpoints, `/api/chat` routing endpoint, and pytest coverage for core flows.
- Rebuilt the Next.js dashboard with pages for the lattice landing experience and trace explorer (list + detail views).
- Shipped the `rajos` Python SDK (client + decorator) so users can instrument any LLM call and push traces locally.
