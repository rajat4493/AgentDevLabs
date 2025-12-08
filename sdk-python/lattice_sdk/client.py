"""
Thin HTTP client for the Lattice Dev Edition API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class CompleteResult:
    text: str
    provider: str
    model: str
    usage: Dict[str, Any]
    cost: Dict[str, Any]
    latency_ms: float
    band: Optional[str] = None
    routing_reason: Optional[str] = None
    tags: List[str] | None = None


class LatticeClient:
    """
    Developer-first HTTP client for `/v1/complete`.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 30.0) -> None:
        default_base = os.getenv("LATTICE_BASE_URL", "http://localhost:8000")
        self.base_url = (base_url or default_base).rstrip("/")
        self.api_key = api_key or os.getenv("LATTICE_API_KEY")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def complete(
        self,
        prompt: str,
        band: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CompleteResult:
        payload = {
            "prompt": prompt,
            "band": band,
            "provider": provider,
            "model": model,
            "metadata": metadata or {},
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/v1/complete", json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        return CompleteResult(
            text=data["text"],
            provider=data["provider"],
            model=data["model"],
            usage=data.get("usage", {}),
            cost=data.get("cost", {}),
            latency_ms=data.get("latency_ms", 0.0),
            band=data.get("band"),
            routing_reason=data.get("routing_reason"),
            tags=data.get("tags"),
        )


__all__ = ["CompleteResult", "LatticeClient"]
