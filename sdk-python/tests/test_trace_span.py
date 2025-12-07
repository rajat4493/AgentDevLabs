from __future__ import annotations

from typing import Any, Dict

from rajos.decorators import trace_span


class FakeClient:
    def __init__(self) -> None:
        self.payloads: list[Dict[str, Any]] = []

    def create_trace(self, **payload: Any) -> Dict[str, Any]:
        self.payloads.append(payload)
        return payload


def test_trace_span_records_payload() -> None:
    fake = FakeClient()

    with trace_span(
        operation="openai.chat",
        provider="openai",
        model="gpt-4.1-mini",
        client=fake,
    ) as span:
        span["input"] = "hello"
        span["output"] = "world"

    assert len(fake.payloads) == 1
    payload = fake.payloads[0]
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["input"] == "hello"
    assert payload["output"] == "world"
    assert isinstance(payload["latency_ms"], int)
