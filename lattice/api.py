"""
FastAPI surface for Lattice v0.3 – Dev Edition.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Dict

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from .cache import CacheDisabled, get_cache
from .config import settings
from .errors import (
    ConfigurationError,
    ProviderInternalError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
    RateLimitExceededError,
    error_response,
)
from .logging import configure_logger
from .metrics import METRICS
from .rate_limit import rate_limiter
from .service import CompleteRequest, complete
logger = configure_logger("lattice.api")

app = FastAPI(
    title="Lattice API",
    description="Local-first routing, cost tracking, and privacy-safe completions.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _log_error(exc: Exception, *, status_code: int, error_type: str) -> None:
    logger.warning(
        "request_failed",
        extra={
            "error_type": error_type,
            "status_code": status_code,
            "detail": getattr(exc, "message", str(exc)),
            "provider": getattr(exc, "provider", None),
        },
    )


def _json_error(exc, status_code: int):
    _log_error(exc, status_code=status_code, error_type=exc.error_type)
    return JSONResponse(status_code=status_code, content=error_response(exc))


def _resolve_consumer_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        if token:
            return token
    client_host = getattr(request.client, "host", None)
    return client_host or "anonymous"


def enforce_rate_limit(request: Request) -> None:
    if not settings.rate_limit_enabled:
        return
    consumer = _resolve_consumer_key(request)
    allowed = rate_limiter.check_and_increment(consumer, settings.rate_limit_per_day, 86_400)
    if not allowed:
        raise RateLimitExceededError("Daily limit exceeded.")


def _readiness_details() -> tuple[bool, Dict[str, str]]:
    details: Dict[str, str] = {}
    ready = True
    if settings.redis_url and not settings.cache_disabled:
        try:
            client = get_cache()
            if not client.ping():
                raise RuntimeError("cache ping failed")
        except CacheDisabled:
            pass
        except Exception:
            ready = False
            details["cache"] = "unreachable"
    provider_keys = [
        settings.openai_api_key,
        settings.anthropic_api_key,
        settings.gemini_api_key,
    ]
    if not any(provider_keys):
        details["providers"] = "no provider API keys configured"
        if settings.environment.lower() in {"prod", "cloud"}:
            ready = False
    return ready, details


@app.exception_handler(ProviderTimeoutError)
async def handle_timeout(request: Request, exc: ProviderTimeoutError):
    return _json_error(exc, status_code=504)


@app.exception_handler(ProviderRateLimitError)
async def handle_rate_limit(request: Request, exc: ProviderRateLimitError):
    return _json_error(exc, status_code=429)


@app.exception_handler(RateLimitExceededError)
async def handle_global_rate_limit(request: Request, exc: RateLimitExceededError):
    return _json_error(exc, status_code=429)


@app.exception_handler(ProviderValidationError)
async def handle_provider_validation(request: Request, exc: ProviderValidationError):
    return _json_error(exc, status_code=400)


@app.exception_handler(ProviderInternalError)
async def handle_provider_internal(request: Request, exc: ProviderInternalError):
    return _json_error(exc, status_code=502)


@app.exception_handler(ConfigurationError)
async def handle_configuration_error(request: Request, exc: ConfigurationError):
    return _json_error(exc, status_code=500)


@app.exception_handler(RequestValidationError)
async def handle_request_validation(request: Request, exc: RequestValidationError):
    _log_error(exc, status_code=422, error_type="request_validation")
    return JSONResponse(
        status_code=422,
        content={"error": {"type": "request_validation", "message": "Invalid request payload."}},
    )


@app.post("/v1/complete")
def post_complete(payload: CompleteRequest, _: None = Depends(enforce_rate_limit)):
    """
    Route a prompt to the configured band/provider without persisting raw text.
    """

    return complete(payload)


@app.get("/v1/metrics")
def get_metrics():
    """
    Return aggregated counters only — no individual prompt data.
    """

    snapshot = METRICS.snapshot()
    return asdict(snapshot)


@app.get("/v1/health")
def get_health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/v1/ready")
def get_ready():
    ready, details = _readiness_details()
    payload = {"status": "ready" if ready else "not_ready"}
    if details:
        payload["details"] = details
    status_code = 200 if ready else 503
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/")
def root():
    """
    Basic index so hitting the root path doesn't 404.
    """

    return {
        "service": "lattice-dev-edition",
        "version": "0.3.0",
        "endpoints": ["/v1/complete", "/v1/metrics", "/v1/health", "/dashboard"],
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """
    Minimal HTML dashboard for quick local verification.
    """

    return HTMLResponse(
        """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Lattice Metrics</title>
    <style>
      body { font-family: system-ui, sans-serif; background: #05060a; color: #f4f4f5; padding: 2rem; }
      pre { background: #0f1117; padding: 1rem; border-radius: 12px; }
    </style>
  </head>
  <body>
    <h1>Lattice Metrics</h1>
    <p>Auto-refreshing snapshot from <code>/v1/metrics</code>.</p>
    <pre id="metrics">Loading...</pre>
    <script>
      async function refresh() {
        try {
          const resp = await fetch('/v1/metrics');
          const data = await resp.json();
          document.getElementById('metrics').textContent = JSON.stringify(data, null, 2);
        } catch (err) {
          document.getElementById('metrics').textContent = 'Failed to load metrics.';
        }
      }
      refresh();
      setInterval(refresh, 5000);
    </script>
  </body>
</html>
        """,
        media_type="text/html",
    )


__all__ = ["app"]
