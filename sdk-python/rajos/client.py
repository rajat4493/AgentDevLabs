"""
HTTP client for the RAJOS backend.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, MutableMapping

import requests
from requests import Session


class RajosClientError(RuntimeError):
    """Raised when the backend cannot be reached."""


class RajosClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = 15.0,
        session: Session | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("RAJOS_BASE_URL") or "http://localhost:8000").rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

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

    def create_trace(self, **trace_payload: Any) -> Dict[str, Any]:
        """
        Create a trace directly via POST /api/traces.
        """
        return self._request("post", "/api/traces", json=trace_payload)

    def route_chat(self, prompt: str, **params: Any) -> Dict[str, Any]:
        """
        Call the router endpoint and receive the model output + trace id.
        """
        payload: Dict[str, Any] = {"prompt": prompt}
        payload.update(params)
        return self._request("post", "/api/chat", json=payload)

    def list_traces(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        **filters: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        params.update({k: v for k, v in filters.items() if v is not None})
        return self._request("get", "/api/traces", params=params)

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "RajosClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()
