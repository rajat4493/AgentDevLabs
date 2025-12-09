"""
Simple per-key rate limiting with Redis or in-memory fallback.
"""

from __future__ import annotations

import time
from threading import Lock
from typing import Dict, Optional

from .config import settings

try:  # pragma: no cover
    import redis  # type: ignore[import]
except ImportError:  # pragma: no cover
    redis = None  # type: ignore[assignment]


class RateLimiter:
    def __init__(self) -> None:
        self._redis = self._init_redis()
        self._lock = Lock()
        self._windows: Dict[str, Dict[str, float]] = {}

    def _init_redis(self):
        if not settings.redis_url or redis is None:
            return None
        try:
            client = redis.Redis.from_url(settings.redis_url)
            client.ping()
            return client
        except Exception:
            return None

    def check_and_increment(self, key: str, limit: int, window_seconds: int) -> bool:
        if limit <= 0 or window_seconds <= 0:
            return True
        if self._redis:
            return self._check_redis(key, limit, window_seconds)
        return self._check_memory(key, limit, window_seconds)

    def _check_redis(self, key: str, limit: int, window_seconds: int) -> bool:
        bucket = f"lattice:rate:{key}:{window_seconds}"
        current = self._redis.incr(bucket)
        if current == 1:
            self._redis.expire(bucket, window_seconds)
        return current <= limit

    def _check_memory(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        window = self._windows.get(key)
        with self._lock:
            window = self._windows.get(key)
            if not window or now - window["start"] >= window_seconds:
                self._windows[key] = {"start": now, "count": 1}
                return True
            if window["count"] >= limit:
                return False
            window["count"] += 1
            return True


rate_limiter = RateLimiter()


__all__ = ["RateLimiter", "rate_limiter"]
