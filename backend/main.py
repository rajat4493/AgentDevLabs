"""
FastAPI entrypoint for the RAJOS backend.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import router as router_api
from backend.api.traces import router as traces_api
from backend.config import get_settings
from backend.db import init_db

settings = get_settings()
init_db()

app = FastAPI(
    title="RAJOS API",
    description="Developer-first tracing + routing backend for RAJOS.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traces_api)
app.include_router(router_api)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "rajos-backend", "environment": settings.environment}


__all__ = ["app"]
