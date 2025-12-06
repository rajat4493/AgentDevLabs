<div align="center">

# RAJOS — the LLM tracing & routing devkit

Energy, movement, flow. RAJOS turns every local LLM experiment into structured traces, friendly dashboards, and debuggable router decisions.

</div>

## Why RAJOS?

- **FastAPI backend** for capturing traces, exposing routing APIs, and storing data locally in SQLite by default.
- **Next.js dashboard** to browse traces (list + detail) without heavy enterprise chrome.
- **Python SDK** (`rajos` package) with a drop-in decorator and lightweight HTTP client so you can instrument LangChain, raw OpenAI calls, or custom agents in minutes.
- **Local-first workflow**: run `uvicorn` + `pnpm dev`, install the SDK with `pip install -e ./sdk-python`, no Docker or multi-tenant setup.

## Repository layout

```
backend/      # FastAPI app, SQLAlchemy models, provider adapters, router logic, tests
sdk-python/   # rajos Python package (client + decorator) and tests
ui/           # Next.js dashboard for landing + traces view
```

## Quick start

1. **Backend**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install fastapi uvicorn sqlalchemy pydantic requests
   uvicorn backend.main:app --reload
   ```
   The API runs on `http://localhost:8000`.

2. **UI**
   ```bash
   cd ui
   pnpm install   # or npm install
   pnpm dev
   ```
   Visit `http://localhost:3000` (set `NEXT_PUBLIC_RAJOS_API_BASE` to point at the backend if you change ports).

3. **Python SDK**
   ```bash
   cd sdk-python
   pip install -e .
   ```
   ```python
   from rajos import trace_llm_call, RajosClient

   @trace_llm_call(provider="openai", model="gpt-4o-mini", framework="raw")
   def ask_llm(prompt: str, *, rajos_metadata=None) -> str:
       return my_openai_call(prompt)

   result = ask_llm("What is RAJOS?", rajos_metadata={"project": "demo"})

   client = RajosClient()
   traces = client.list_traces(limit=5)
   ```

## Backend highlights

- `backend/main.py` starts FastAPI, wires CORS, and exposes `/health`, `/api/traces`, and `/api/chat`.
- `backend/models.py` defines `Trace` with provider, model, inputs/outputs, latency, and JSON metadata.
- `backend/api/traces.py` provides CRUD endpoints with pagination + filters.
- `backend/api/router.py` reuses the existing routing logic (`backend/router/…`) and provider adapters to execute calls and automatically persist traces.
- Default storage is SQLite (`rajos.db`). Override via `RAJOS_DATABASE_URL`.

### Useful environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `RAJOS_DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./rajos.db` |
| `RAJOS_CORS_ORIGINS` | Comma-separated origins for CORS | `http://localhost:3000` |
| `RAJOS_ENV` | Environment label for health checks | `development` |
| `NEXT_PUBLIC_RAJOS_API_BASE` | UI → API base URL | `http://localhost:8000` |
| `RAJOS_BASE_URL` | SDK client base URL | `http://localhost:8000` |

### Provider credentials

Adapters live in `backend/providers/`. Set env vars such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or run against the included `stub` provider when developing offline (`provider="stub"`, `model="stub-echo-1"`).

## Python SDK tips

- `RajosClient.create_trace(**payload)` mirrors the backend schema for direct inserts.
- `RajosClient.route_chat(prompt, **kwargs)` hits `/api/chat` to leverage routing logic and returns `trace_id`.
- `trace_llm_call` accepts optional `extra` metadata and will also merge a `rajos_metadata` dict passed into the wrapped function (the kwarg is stripped before your function executes).
- Network failures fail open—the decorator never raises if the backend is offline.

## UI overview

- `ui/pages/index.tsx` is a lightweight hero page explaining RAJOS and how to get started locally.
- `ui/pages/traces/index.tsx` fetches the most recent traces from the backend and renders them with filtering-ready tables.
- `ui/pages/traces/[id].tsx` shows the full prompt/output plus JSON metadata for a single trace.

## Testing

Backend and SDK tests rely on `pytest`:

```bash
pytest backend/tests sdk-python/tests
```

(`pytest` is not bundled; install it in your virtualenv.)

## Roadmap & changelog

- See [`ROADMAP.md`](ROADMAP.md) for upcoming work.
- See [`CHANGELOG.md`](CHANGELOG.md) for release notes.
