# Changelog

## [0.1.0] - 2024-12-07

- Pivoted the repo into the RAJOS developer-first toolkit with a clean `backend/`, `ui/`, and `sdk-python/` layout.
- Reused the existing routing logic + provider adapters inside a new FastAPI app that stores traces locally in SQLite.
- Added `/api/traces` CRUD endpoints, `/api/chat` routing endpoint, and pytest coverage for core flows.
- Rebuilt the Next.js dashboard with pages for the RAJOS landing experience and trace explorer (list + detail views).
- Shipped the `rajos` Python SDK (client + decorator) so users can instrument any LLM call and push traces locally.
