from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import pytest

from rajos.decorators import trace_llm_call


@dataclass
class DummyClient:
    traces: List[Dict[str, Any]] = field(default_factory=list)

    def create_trace(self, **payload: Any) -> Dict[str, Any]:
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
