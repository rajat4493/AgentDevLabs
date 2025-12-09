"""
Aggregated metrics for the Lattice Dev Edition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional

from .config import settings

try:  # pragma: no cover
    import redis  # type: ignore[import]
except ImportError:  # pragma: no cover
    redis = None  # type: ignore[assignment]


@dataclass
class MetricsSnapshot:
    total_requests: int
    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    average_latency_ms: float
    cache_hits_total: int
    cache_misses_total: int
    pii_detected_total: int
    providers: Dict[str, int] = field(default_factory=dict)
    models: Dict[str, int] = field(default_factory=dict)
    bands: Dict[str, int] = field(default_factory=dict)


class BaseMetricsBackend:
    def increment_requests(
        self,
        *,
        provider: str,
        model: str,
        band: Optional[str],
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        pii_tags_count: int,
    ) -> None:
        raise NotImplementedError

    def increment_cache_hit(self) -> None:
        raise NotImplementedError

    def increment_cache_miss(self) -> None:
        raise NotImplementedError

    def snapshot(self) -> MetricsSnapshot:
        raise NotImplementedError


class InMemoryMetricsBackend(BaseMetricsBackend):
    def __init__(self) -> None:
        self._lock = Lock()
        self._total_requests = 0
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._latency_sum_ms = 0.0
        self._latency_samples = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._pii_detected = 0
        self._providers: Dict[str, int] = {}
        self._models: Dict[str, int] = {}
        self._bands: Dict[str, int] = {}

    def _increment_bucket(self, bucket: Dict[str, int], key: Optional[str]) -> None:
        if not key:
            return
        bucket[key] = bucket.get(key, 0) + 1

    def increment_requests(
        self,
        *,
        provider: str,
        model: str,
        band: Optional[str],
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        pii_tags_count: int,
    ) -> None:
        with self._lock:
            self._total_requests += 1
            self._latency_sum_ms += float(latency_ms)
            self._latency_samples += 1
            self._total_input_tokens += int(input_tokens)
            self._total_output_tokens += int(output_tokens)
            self._total_cost += float(total_cost)
            self._increment_bucket(self._providers, provider)
            self._increment_bucket(self._models, model)
            self._increment_bucket(self._bands, band)
            if pii_tags_count > 0:
                self._pii_detected += 1

    def increment_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def increment_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            avg_latency = (
                self._latency_sum_ms / self._latency_samples if self._latency_samples else 0.0
            )
            return MetricsSnapshot(
                total_requests=self._total_requests,
                total_cost=round(self._total_cost, 8),
                total_input_tokens=self._total_input_tokens,
                total_output_tokens=self._total_output_tokens,
                average_latency_ms=round(avg_latency, 4),
                cache_hits_total=self._cache_hits,
                cache_misses_total=self._cache_misses,
                pii_detected_total=self._pii_detected,
                providers=dict(self._providers),
                models=dict(self._models),
                bands=dict(self._bands),
            )


class RedisMetricsBackend(BaseMetricsBackend):
    def __init__(self, client: "redis.Redis") -> None:
        self._client = client
        self._counts_key = "lattice:metrics:counts"
        self._providers_key = "lattice:metrics:providers"
        self._models_key = "lattice:metrics:models"
        self._bands_key = "lattice:metrics:bands"

    def increment_requests(
        self,
        *,
        provider: str,
        model: str,
        band: Optional[str],
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        pii_tags_count: int,
    ) -> None:
        pipe = self._client.pipeline()
        pipe.hincrby(self._counts_key, "total_requests", 1)
        pipe.hincrbyfloat(self._counts_key, "total_cost", float(total_cost))
        pipe.hincrby(self._counts_key, "total_input_tokens", int(input_tokens))
        pipe.hincrby(self._counts_key, "total_output_tokens", int(output_tokens))
        pipe.hincrbyfloat(self._counts_key, "latency_sum_ms", float(latency_ms))
        pipe.hincrby(self._counts_key, "latency_samples", 1)
        if pii_tags_count > 0:
            pipe.hincrby(self._counts_key, "pii_detected_total", 1)
        pipe.hincrby(self._providers_key, provider, 1)
        pipe.hincrby(self._models_key, model, 1)
        if band:
            pipe.hincrby(self._bands_key, band, 1)
        pipe.execute()

    def increment_cache_hit(self) -> None:
        self._client.hincrby(self._counts_key, "cache_hits_total", 1)

    def increment_cache_miss(self) -> None:
        self._client.hincrby(self._counts_key, "cache_misses_total", 1)

    def snapshot(self) -> MetricsSnapshot:
        counts = self._client.hgetall(self._counts_key)
        providers = {k: int(v) for k, v in self._client.hgetall(self._providers_key).items()}
        models = {k: int(v) for k, v in self._client.hgetall(self._models_key).items()}
        bands = {k: int(v) for k, v in self._client.hgetall(self._bands_key).items()}
        latency_sum = float(counts.get("latency_sum_ms", 0.0))
        latency_samples = int(counts.get("latency_samples", 0))
        avg_latency = latency_sum / latency_samples if latency_samples else 0.0
        return MetricsSnapshot(
            total_requests=int(counts.get("total_requests", 0)),
            total_cost=float(counts.get("total_cost", 0.0)),
            total_input_tokens=int(counts.get("total_input_tokens", 0)),
            total_output_tokens=int(counts.get("total_output_tokens", 0)),
            average_latency_ms=round(avg_latency, 4),
            cache_hits_total=int(counts.get("cache_hits_total", 0)),
            cache_misses_total=int(counts.get("cache_misses_total", 0)),
            pii_detected_total=int(counts.get("pii_detected_total", 0)),
            providers=providers,
            models=models,
            bands=bands,
        )


class Metrics:
    def __init__(self) -> None:
        self._backend = self._select_backend()

    def _select_backend(self) -> BaseMetricsBackend:
        if settings.redis_url and redis is not None:
            try:
                client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                client.ping()
                return RedisMetricsBackend(client)
            except Exception:
                pass
        return InMemoryMetricsBackend()

    def increment_requests(
        self,
        *,
        provider: str,
        model: str,
        band: Optional[str],
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        pii_tags_count: int,
    ) -> None:
        self._backend.increment_requests(
            provider=provider,
            model=model,
            band=band,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
            pii_tags_count=pii_tags_count,
        )

    def increment_cache_hit(self) -> None:
        self._backend.increment_cache_hit()

    def increment_cache_miss(self) -> None:
        self._backend.increment_cache_miss()

    def snapshot(self) -> MetricsSnapshot:
        try:
            return self._backend.snapshot()
        except Exception:  # pragma: no cover - safety net
            return MetricsSnapshot(
                total_requests=0,
                total_cost=0.0,
                total_input_tokens=0,
                total_output_tokens=0,
                average_latency_ms=0.0,
                cache_hits_total=0,
                cache_misses_total=0,
                pii_detected_total=0,
            )


METRICS = Metrics()


__all__ = ["Metrics", "MetricsSnapshot", "METRICS"]
