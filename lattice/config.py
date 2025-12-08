"""
Dev-friendly configuration for the Lattice backend.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List


class Settings:
    """
    Minimal settings object backed by environment variables.

    All vars are prefixed with LATTICE_ to avoid collisions.
    """

    def __init__(self) -> None:
        cors_origins = os.getenv("LATTICE_CORS_ORIGINS", "http://localhost:3000")
        self.cors_origins: List[str] = [
            origin.strip() for origin in cors_origins.split(",") if origin.strip()
        ]
        self.environment = os.getenv("LATTICE_ENV", "dev")
        self.cache_disabled = os.getenv("LATTICE_CACHE_DISABLED") == "1"
        self.cache_prefix = os.getenv("LATTICE_CACHE_PREFIX", "lattice:cache")
        self.cache_ttl_seconds = int(os.getenv("LATTICE_CACHE_TTL_SECONDS", "60"))
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.bands_file = os.getenv(
            "LATTICE_BANDS_FILE",
            str(os.path.join(os.path.dirname(__file__), "data", "bands.json")),
        )
        self.pricing_file = os.getenv(
            "LATTICE_PRICING_FILE",
            str(os.path.join(os.path.dirname(__file__), "data", "pricing.json")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
