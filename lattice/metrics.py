"""
In-memory aggregated metrics for the Lattice Dev Edition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Iterable, List, Optional


def _is_sensitive_tag(tag: str) -> bool:
    upper = tag.upper()
    return upper.startswith("PII") or upper.startswith("PHI")


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


class MetricsCollector:
    """
    Thread-safe counters for aggregated metrics.
    """

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

    def _increment(self, bucket: Dict[str, int], key: Optional[str]) -> None:
        if not key:
            return
        bucket[key] = bucket.get(key, 0) + 1

    def record_request(
        self,
        *,
        provider: str,
        model: str,
        band: Optional[str],
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        cache_hit: bool,
        tags: Optional[Iterable[str]] = None,
        count_usage: bool = True,
    ) -> None:
        """
        Record a routed completion. `count_usage` should be False for cache hits so
        tokens/cost are not double-counted.
        """

        with self._lock:
            self._total_requests += 1
            self._latency_sum_ms += float(latency_ms)
            self._latency_samples += 1
            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

            self._increment(self._providers, provider)
            self._increment(self._models, model)
            self._increment(self._bands, band)

            if count_usage:
                self._total_input_tokens += int(input_tokens)
                self._total_output_tokens += int(output_tokens)
                self._total_cost += float(total_cost)

            if tags:
                if any(_is_sensitive_tag(tag) for tag in tags):
                    self._pii_detected += 1

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


METRICS = MetricsCollector()


__all__ = ["MetricsCollector", "MetricsSnapshot", "METRICS"]
