"""
Redis-backed cache helpers for the lattice backend router.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

try:  # pragma: no cover - optional dependency is validated at runtime
    import redis  # type: ignore[import]
except ImportError:  # pragma: no cover
    redis = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover
    from redis import Redis


class CacheDisabled(Exception):
    """Raised when cache is not configured or intentionally disabled."""


class CacheClient:
    """
    Thin wrapper around Redis for exact-match cache.
    """

    def __init__(self, redis_client: "redis.Redis", prefix: str, ttl_seconds: int) -> None:
        self._redis = redis_client
        self._prefix = prefix.rstrip(":")
        self._ttl_seconds = ttl_seconds

    @classmethod
    def from_env(cls) -> "CacheClient":
        from .config import get_settings

        settings = get_settings()
        if settings.cache_disabled:
            raise CacheDisabled("Lattice cache disabled via env var.")

        if redis is None:
            raise CacheDisabled("redis package is not installed.")

        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        return cls(redis_client=client, prefix=settings.cache_prefix, ttl_seconds=settings.cache_ttl_seconds)

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        full_key = self._full_key(key)
        value = self._redis.get(full_key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        full_key = self._full_key(key)
        if is_dataclass(value):
            payload = asdict(value)
        else:
            payload = value
        ttl = ttl_seconds or self._ttl_seconds
        self._redis.set(full_key, json.dumps(payload), ex=ttl)


_CACHE_CLIENT: Optional[CacheClient] = None
_CACHE_ENABLED: Optional[bool] = None


def get_cache_client() -> CacheClient:
    """
    Lazily get a singleton CacheClient or raise CacheDisabled.
    """

    global _CACHE_CLIENT, _CACHE_ENABLED

    if _CACHE_ENABLED is False:
        raise CacheDisabled("Cache previously determined as disabled.")

    if _CACHE_CLIENT is not None:
        return _CACHE_CLIENT

    try:
        _CACHE_CLIENT = CacheClient.from_env()
        _CACHE_ENABLED = True
        return _CACHE_CLIENT
    except CacheDisabled:
        _CACHE_ENABLED = False
        raise
    except Exception:  # pragma: no cover - defensive fallback
        _CACHE_ENABLED = False
        raise CacheDisabled("Cache unavailable (connection failure).")


def build_exact_cache_key(payload: Dict[str, Any]) -> str:
    """
    Deterministically build a SHA256-based cache key from a payload.
    """

    payload = dict(payload)
    payload.pop("metadata", None)

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"exact:{digest}"


__all__ = ["CacheClient", "CacheDisabled", "build_exact_cache_key", "get_cache_client"]
