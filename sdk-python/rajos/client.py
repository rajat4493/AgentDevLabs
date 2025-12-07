"""
HTTP client for the RAJOS backend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional

import requests
from requests import Session

from . import config


class RajosClientError(RuntimeError):
    """Raised when the backend cannot be reached."""


@dataclass
class ChatRouteResult:
    """
    Structured response from the router endpoint.
    """

    content: str
    provider: str
    model: str
    usage: Dict[str, int]
    cost: Dict[str, Any]
    trace_id: int
    latency_ms: Optional[int] = None
    band: Optional[str] = None
    route_source: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @property
    def total_cost(self) -> Optional[float]:
        if not self.cost:
            return None
        value = self.cost.get("total_cost")
        return float(value) if value is not None else None


class RajosClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        session: Session | None = None,
    ) -> None:
        resolved_base = base_url or os.getenv("RAJOS_BASE_URL") or config.BASE_URL
        self.base_url = resolved_base.rstrip("/")
        self.api_key = api_key if api_key is not None else config.API_KEY
        self.timeout = timeout if timeout is not None else config.TIMEOUT
        self.session = session or requests.Session()
        self._last_result: Optional[ChatRouteResult] = None

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = self._url(path)
        try:
            resp = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:  # pragma: no cover - network errors
            raise RajosClientError(str(exc)) from exc
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise RajosClientError(f"{resp.status_code} error: {resp.text}") from exc
        if resp.content:
            return resp.json()
        return {}

    def _chat_payload(self, prompt: str, overrides: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"prompt": prompt}
        if overrides:
            payload.update({k: v for k, v in overrides.items() if v is not None})
        return payload

    def _parse_chat_result(self, data: Mapping[str, Any]) -> ChatRouteResult:
        usage = {
            "total_tokens": int(data.get("tokens") or 0),
            "input_tokens": int(data.get("prompt_tokens") or 0),
            "output_tokens": int(data.get("completion_tokens") or 0),
        }
        cost_payload = dict(data.get("cost") or {})
        if not cost_payload and data.get("cost_usd") is not None:
            cost_payload = {"currency": "USD", "total_cost": data.get("cost_usd")}

        result = ChatRouteResult(
            content=str(data.get("output") or ""),
            provider=str(data.get("provider") or ""),
            model=str(data.get("model") or ""),
            usage=usage,
            cost=cost_payload,
            trace_id=int(data.get("trace_id") or 0),
            latency_ms=data.get("latency_ms"),
            band=data.get("band"),
            route_source=data.get("route_source"),
            meta={"raw": dict(data)},
        )
        self._last_result = result
        return result

    def _auth_headers(self) -> MutableMapping[str, str]:
        headers: MutableMapping[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def create_trace(self, **trace_payload: Any) -> Dict[str, Any]:
        """
        Create a trace directly via POST /api/traces.
        """
        return self._request("post", "/api/traces", json=trace_payload, headers=self._auth_headers())

    def log_trace(
        self,
        *,
        provider: str,
        model: str,
        input: str,
        output: str,
        tokens: int | None = None,
        latency_ms: int | None = None,
        framework: str = "raw",
        source: str = "sdk",
        extra: Dict[str, Any] | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "provider": provider,
            "model": model,
            "input": input,
            "output": output,
            "tokens": tokens,
            "latency_ms": latency_ms,
            "framework": framework,
            "source": source,
            "extra": extra,
            "status": status,
            "error_message": error_message,
        }
        return self.create_trace(**payload)

    def route_chat(self, prompt: str, **params: Any) -> Dict[str, Any]:
        """
        Call the router endpoint and receive the model output + trace id.
        """
        payload = self._chat_payload(prompt, params)
        headers = self._auth_headers()
        return self._request("post", "/api/chat", json=payload, headers=headers)

    def complete(self, prompt: str, **params: Any) -> ChatRouteResult:
        """
        Same as route_chat but returns a structured ChatRouteResult with cost info.
        """
        data = self.route_chat(prompt, **params)
        return self._parse_chat_result(data)

    @property
    def last_cost(self) -> Optional[Dict[str, Any]]:
        if self._last_result:
            return self._last_result.cost
        return None

    def list_traces(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        **filters: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        params.update({k: v for k, v in filters.items() if v is not None})
        return self._request("get", "/api/traces", params=params, headers=self._auth_headers())

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "RajosClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()
