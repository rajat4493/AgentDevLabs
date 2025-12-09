<div align="center">

# Lattice v0.3 — Dev Edition

Privacy-first routing, cost tracking, and tagging for local LLM experiments. No prompt storage, no multi-tenant baggage.

</div>

## Why Lattice?

- **No prompt/response storage.** `/v1/complete` routes to OpenAI, Anthropic, Gemini, Ollama, or the stub adapter without writing raw text to disk. Only aggregate counters are kept.
- **Aggregated metrics only.** `/v1/metrics` reports totals for requests, tokens, cost, latency, cache hits/misses, provider/band usage, and PII/PHI hits.
- **Short-lived cache.** Optional Redis cache stores final responses for ~60 seconds (hashing prompt+model) to keep dev loops fast without long-term retention.
- **Regex-based PII tags.** `lattice.pii.detect_tags` flags email/phone/credit-card patterns plus PHI/financial keywords and surfaces them as tags instead of logging text.
- **Dev-friendly SDK.** `lattice_sdk` ships a single `LatticeClient.complete()` helper that returns text, usage, cost, latency, and tags.

## Repository layout

```
lattice/       # FastAPI app, router, metrics, cache, PII tagging, provider adapters
sdk-python/    # lattice_sdk Python package + backwards-compatible rajos shim
ui/            # Legacy Next.js dashboard (optional; /dashboard HTML is built into the API)
```

## Quick start

1. **Backend**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install fastapi uvicorn requests redis pydantic httpx
   export OPENAI_API_KEY=...
   uvicorn lattice.api:app --reload
   ```
   - POST `/v1/complete` with `{"prompt": "...", "band": "low"}`.
   - GET `/v1/metrics` for aggregated counters.
   - Visit `/dashboard` for a simple auto-refreshing HTML view.

2. **SDK**
   ```bash
   cd sdk-python
   pip install -e .
   python
   ```
   ```python
   from lattice_sdk import LatticeClient

   client = LatticeClient()
   result = client.complete("Explain lattice in 3 bullet points.", band="mid")
   print(result.text, result.cost["total_cost"], result.tags)
   ```

## Core API surface

| Endpoint | Description |
| --- | --- |
| `POST /v1/complete` | Routes a prompt, enforces band/model, TTL cache, computes cost + tags. Returns `{text, usage, cost, latency_ms, band, routing_reason, tags}`. |
| `GET /v1/metrics` | Returns aggregated metrics only (no per-request rows). |
| `GET /v1/health` | `{ "status": "ok" }` heartbeat. |
| `GET /v1/ready` | Checks cache/provider readiness; 503 when dependencies fail. |
| `GET /dashboard` | Minimal HTML view that polls `/v1/metrics`. |

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / ... | Adapter credentials | _required per provider_ |
| `LATTICE_ENV` | Label for `/v1/health` | `dev` |
| `LATTICE_CORS_ORIGINS` | Comma-separated origins for FastAPI CORS | `http://localhost:3000` |
| `LATTICE_CACHE_DISABLED` | Set to `1` to disable Redis cache | `0` |
| `LATTICE_CACHE_TTL_SECONDS` | Cache TTL for `/v1/complete` payloads | `60` |
| `LATTICE_CACHE_PREFIX` | Redis key prefix | `lattice:cache` |
| `BANDS_CONFIG_PATH` | Path to `bands.json` for routing | `lattice/data/bands.json` |
| `LATTICE_PRICING_FILE` | Path to `pricing.json` for cost | `lattice/data/pricing.json` |
| `LATTICE_RATE_LIMIT_ENABLED` | Enable per-key/IP rate limiting | `0` |
| `LATTICE_RATE_LIMIT_PER_DAY` | Requests per 24h window when enabled | `1000` |
| `REDIS_URL` | Cache + rate limit backend | `redis://localhost:6379/0` |

## Invariants enforced in code

- The server never persists prompt or response text in any DB/log. Cache entries only keep the response payload for a short TTL.
- No API keys are stored—providers read from env vars or per-request headers.
- Metrics collector (`lattice.metrics.METRICS`) only tracks aggregate counters and tags.

## Reuse + Extensibility

- `lattice/router/bands.py` and `lattice/router/complexity.py` keep the original RAJOS routing heuristics but without tenanting/ALRI baggage.
- `lattice/cache.py` reuses the Redis helper with hashed keys + short TTLs.
- `lattice/providers/` contains adapters for OpenAI, Anthropic, Gemini, Ollama, and a stub echo model.
- `lattice/service.complete()` orchestrates routing, caching, provider calls, cost calculation, tagging, and metrics.

## SDK recap

- Package name: **`lattice-sdk`** (PyPI-safe).
- Module: `lattice_sdk`.
- Entrypoint: `LatticeClient.complete(...) -> CompleteResult`.
- Legacy imports (`import rajos`) continue to work via a shim that re-exports the new client.

## Development tips

- Run `uvicorn lattice.api:app --reload`.
- Use `curl localhost:8000/v1/complete -d '{"prompt":"..."}' -H 'Content-Type: application/json'`.
- Toggle caching with `LATTICE_CACHE_DISABLED=1`.
- Update routing by editing `lattice/data/bands.json` or pointing `LATTICE_BANDS_FILE` to a custom file.

## Roadmap & changelog

- See [`ROADMAP.md`](ROADMAP.md) for upcoming experiments.
- See [`CHANGELOG.md`](CHANGELOG.md) for release notes.
