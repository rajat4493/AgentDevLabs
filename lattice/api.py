"""
FastAPI surface for Lattice v0.3 – Dev Edition.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import get_settings
from .metrics import METRICS
from .service import CompleteRequest, complete

settings = get_settings()

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


@app.post("/v1/complete")
def post_complete(payload: CompleteRequest):
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
