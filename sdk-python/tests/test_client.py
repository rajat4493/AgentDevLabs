from __future__ import annotations

from typing import Any, Dict, List

import requests
import pytest

from rajos.client import RajosClient, RajosClientError


class DummyResponse:
    def __init__(self, status_code: int = 200, payload: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = "error"
        self.content = b"{}"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self) -> Dict[str, Any]:
        return self._payload


class DummySession:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.response_payload: Dict[str, Any] | None = None

    def request(self, *, method: str, url: str, timeout: float, **kwargs: Any) -> DummyResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        payload = self.response_payload or {"ok": True, "method": method}
        return DummyResponse(payload=payload)

    def close(self) -> None:
        pass


def test_client_posts_trace_payload() -> None:
    session = DummySession()
    client = RajosClient(base_url="http://localhost:9999", session=session)
    resp = client.log_trace(provider="stub", model="stub-echo-1", input="hi", output="bye")
    assert resp["ok"] is True
    call = session.calls[0]
    assert call["method"] == "post"
    assert call["url"].endswith("/api/traces")
    assert call["kwargs"]["json"]["status"] == "success"


def test_client_raises_on_http_error() -> None:
    class ErrorSession(DummySession):
        def request(self, *, method: str, url: str, timeout: float, **kwargs: Any) -> DummyResponse:
            return DummyResponse(status_code=500)

    client = RajosClient(session=ErrorSession())
    with pytest.raises(RajosClientError):
        client.list_traces()


def test_complete_returns_structured_result() -> None:
    session = DummySession()
    session.response_payload = {
        "output": "Stub result",
        "provider": "stub",
        "model": "stub-echo-1",
        "tokens": 5,
        "prompt_tokens": 2,
        "completion_tokens": 3,
        "cost": {"currency": "USD", "total_cost": 0.000003},
        "trace_id": 12,
        "band": "low",
        "route_source": "router",
    }
    client = RajosClient(session=session)
    result = client.complete("hello world")
    assert result.content == "Stub result"
    assert result.usage["input_tokens"] == 2
    assert result.cost["total_cost"] == 0.000003
    assert client.last_cost == result.cost
