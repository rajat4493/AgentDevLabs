"""
Cache helpers for storing short-lived responses.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Dict, Optional

from .config import settings

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore[import]
except ImportError:  # pragma: no cover
    redis = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover
    from redis import Redis


class CacheDisabled(Exception):
    """Raised when cache is not configured or intentionally disabled."""


class CacheClient:
    """
    Thin wrapper around Redis for hashed payload cache.
    """

    def __init__(self, redis_client: "redis.Redis", prefix: str, ttl_seconds: int) -> None:
        self._redis = redis_client
        self._prefix = prefix.rstrip(":")
        self._ttl_seconds = ttl_seconds

    @classmethod
    def create(cls) -> "CacheClient":
        if settings.cache_disabled:
            raise CacheDisabled("Lattice cache disabled via env var.")
        if not settings.redis_url or redis is None:
            raise CacheDisabled("Redis cache not configured.")
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        return cls(client, prefix=settings.cache_prefix, ttl_seconds=settings.cache_ttl_seconds)

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        value = self._redis.get(self._full_key(key))
        if value is None:
            return None
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self._ttl_seconds
        self._redis.set(self._full_key(key), json.dumps(value), ex=ttl)

    def ping(self) -> bool:
        try:
            return bool(self._redis.ping())
        except Exception:
            return False


_CACHE_CLIENT: Optional[CacheClient] = None
_CACHE_ENABLED: Optional[bool] = None


def get_cache() -> CacheClient:
    """
    Lazily get a singleton CacheClient or raise CacheDisabled.
    """

    global _CACHE_CLIENT, _CACHE_ENABLED

    if _CACHE_ENABLED is False:
        raise CacheDisabled("Cache previously determined as disabled.")

    if _CACHE_CLIENT is not None:
        return _CACHE_CLIENT

    try:
        _CACHE_CLIENT = CacheClient.create()
        _CACHE_ENABLED = True
        return _CACHE_CLIENT
    except CacheDisabled:
        _CACHE_ENABLED = False
        raise
    except Exception:  # pragma: no cover - defensive fallback
        _CACHE_ENABLED = False
        raise CacheDisabled("Cache unavailable (connection failure).")


def make_cache_key(prompt: str, provider: Optional[str], model: Optional[str], band: Optional[str]) -> str:
    """Hash prompt + routing parameters into a deterministic cache key."""

    payload: Dict[str, Any] = {
        "prompt": prompt.strip(),
        "provider": (provider or "").lower(),
        "model": model,
        "band": band,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"exact:{digest}"


# Backwards compatibility helpers
def get_cache_client() -> CacheClient:
    return get_cache()


def build_exact_cache_key(payload: Dict[str, Any]) -> str:
    return make_cache_key(
        prompt=payload.get("prompt", ""),
        provider=payload.get("provider"),
        model=payload.get("model"),
        band=payload.get("band"),
    )


__all__ = ["CacheDisabled", "CacheClient", "get_cache", "get_cache_client", "make_cache_key"]
