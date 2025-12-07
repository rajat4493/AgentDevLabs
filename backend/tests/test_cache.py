from __future__ import annotations

from backend.cache import CacheClient, build_exact_cache_key


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value


def test_build_exact_cache_key_deterministic() -> None:
    base = {"prompt": "hello", "band": "low", "metadata": {"ignored": True}}
    key1 = build_exact_cache_key(base)
    key2 = build_exact_cache_key({"band": "low", "prompt": "hello"})
    assert key1 == key2


def test_cache_client_roundtrip() -> None:
    cache = CacheClient(redis_client=DummyRedis(), prefix="rajos:test")
    cache.set_json("foo", {"value": 42}, ttl_seconds=60)
    assert cache.get_json("foo") == {"value": 42}
