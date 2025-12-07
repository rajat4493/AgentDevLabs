"""
FastAPI entrypoint for the RAJOS backend.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

if __package__ is None or __package__ == "":
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import router as router_api
from backend.api.traces import router as traces_api
from backend.config import get_settings
from backend.db import engine
from backend.models import Base

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="RAJOS API",
    description="Developer-first tracing + routing backend for RAJOS.",
    version="0.1.0",
    lifespan=lifespan,
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
