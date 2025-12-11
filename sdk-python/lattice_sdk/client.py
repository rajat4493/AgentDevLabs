"""
Thin HTTP client for the Lattice Dev Edition API.

Example:

    from lattice_sdk import LatticeClient

    client = LatticeClient()
    result = client.complete("hello lattice!")
    print(result.text, result.cost["total_cost"], result.routing["reason"])
"""

from __future__ import annotations

import os
import time
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
    tags: List[str] | None = None
    routing: Optional[Dict[str, Any]] = None
    routing_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.routing_reason is None and self.routing:
            self.routing_reason = self.routing.get("reason")


class LatticeAPIError(Exception):
    def __init__(self, message: str, *, error_type: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


class LatticeClient:
    """
    Developer-first HTTP client for `/v1/complete`.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        default_base = os.getenv("LATTICE_BASE_URL", "http://localhost:8000")
        self.base_url = (base_url or default_base).rstrip("/")
        self.api_key = api_key or os.getenv("LATTICE_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request_with_retries(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        delay = 0.5
        attempt = 0
        while True:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(f"{self.base_url}/v1/complete", json=payload, headers=self._headers())
            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise LatticeAPIError(str(exc), error_type="network_error", status_code=0) from exc
                time.sleep(delay)
                delay *= 2
                attempt += 1
                continue

            if resp.status_code == 429 and attempt < self.max_retries:
                time.sleep(delay)
                delay *= 2
                attempt += 1
                continue

            if resp.status_code >= 400:
                raise self._build_error(resp)
            try:
                return resp.json()
            except ValueError as exc:
                raise LatticeAPIError("Malformed JSON response from Lattice.", error_type="invalid_response", status_code=resp.status_code) from exc

    def _build_error(self, response: httpx.Response) -> LatticeAPIError:
        try:
            payload = response.json()
            error_info = payload.get("error") or {}
            message = error_info.get("message", "Lattice API request failed.")
            error_type = error_info.get("type", "api_error")
        except ValueError:
            message = "Lattice API request failed."
            error_type = "api_error"
        return LatticeAPIError(message, error_type=error_type, status_code=response.status_code)

    def complete(
        self,
        prompt: str,
        band: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CompleteResult:
        """
        Route a prompt through the local Lattice router and return structured metadata.

        Example:
            client = LatticeClient()
            res = client.complete("Explain quantum computing like I'm five", band="low")
            print(res.text, res.cost["total_cost"], res.routing["reason"])
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "band": band,
            "model": model,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        payload["metadata"] = metadata if metadata is not None else None

        data = self._request_with_retries(payload)
        routing = data.get("routing")

        return CompleteResult(
            text=data["text"],
            provider=data["provider"],
            model=data["model"],
            usage=data.get("usage", {}),
            cost=data.get("cost", {}),
            latency_ms=data.get("latency_ms", 0.0),
            band=data.get("band"),
            tags=data.get("tags"),
            routing=routing,
            routing_reason=(routing or {}).get("reason"),
        )


__all__ = ["CompleteResult", "LatticeClient", "LatticeAPIError"]
