from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import pytest

from rajos.client import RajosClient
from rajos.decorators import trace_llm_call, trace_span


@dataclass
class DummyClient:
    traces: List[Dict[str, Any]] = field(default_factory=list)

    def log_trace(self, **payload: Any) -> Dict[str, Any]:
        self.traces.append(payload)
        return {"id": f"t_{len(self.traces)}"}


def test_trace_llm_call_records_successful_call() -> None:
    client = DummyClient()

    @trace_llm_call(provider="stub", model="stub-echo-1", client=client, extra={"env": "test"})
    def echo(prompt: str, *, suffix: str = "", rajos_metadata: Dict[str, Any] | None = None) -> str:
        return f"{prompt}{suffix}"

    result = echo("hello", suffix=" world", rajos_metadata={"tags": ["unit"]})
    assert result == "hello world"
    assert len(client.traces) == 1
    trace = client.traces[0]
    assert trace["input"] == "hello"
    assert trace["output"] == "hello world"
    assert trace["extra"]["env"] == "test"
    assert trace["extra"]["tags"] == ["unit"]
    assert trace["status"] == "success"


def test_trace_llm_call_records_exceptions() -> None:
    client = DummyClient()

    @trace_llm_call(provider="stub", model="stub-echo-1", client=client)
    def explode(prompt: str) -> str:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        explode("fail")

    assert len(client.traces) == 1
    trace = client.traces[0]
    assert trace["extra"]["decorator"]["function"].endswith("explode")
    assert "Exception:" in trace["output"]
    assert trace["status"] == "error"
    assert "RuntimeError" in (trace["error_message"] or "")


def test_trace_llm_call_uses_provided_client_and_handles_logging_errors() -> None:
    class FailingClient(DummyClient):
        def log_trace(self, **payload: Any) -> Dict[str, Any]:
            raise RuntimeError("boom")

    client = FailingClient()

    @trace_llm_call(provider="stub", model="stub-echo-1", client=client)
    def echo(prompt: str) -> str:
        return prompt.upper()

    assert echo("hi") == "HI"


def test_trace_llm_call_logs_error_status_before_raising() -> None:
    client = DummyClient()

    @trace_llm_call(provider="stub", model="stub-echo-1", client=client)
    def fail(prompt: str) -> str:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        fail("x")

    assert client.traces[0]["status"] == "error"
    assert "ValueError" in (client.traces[0]["error_message"] or "")
