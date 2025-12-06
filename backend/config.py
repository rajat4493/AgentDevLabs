"""
Configuration helpers for the RAJOS backend.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List


class Settings:
    """
    Minimal settings object backed by environment variables.

    All vars are prefixed with RAJOS_ to avoid conflicts.
    """

    def __init__(self) -> None:
        self.database_url = os.getenv("RAJOS_DATABASE_URL", "sqlite:///./rajos.db")
        cors_origins = os.getenv("RAJOS_CORS_ORIGINS", "http://localhost:3000")
        self.cors_origins: List[str] = [
            origin.strip() for origin in cors_origins.split(",") if origin.strip()
        ]
        self.environment = os.getenv("RAJOS_ENV", "development")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
