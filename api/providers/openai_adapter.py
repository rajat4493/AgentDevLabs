import os
import time
from typing import Any, Dict

from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


OPENAI_PRICING_PER_1M = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def _estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = OPENAI_PRICING_PER_1M.get(model)
    if not pricing:
        return 0.0
    cost_input = (prompt_tokens / 1_000_000) * pricing["input"]
    cost_output = (completion_tokens / 1_000_000) * pricing["output"]
    return round(cost_input + cost_output, 8)


def plan(run_payload: Dict[str, Any], model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    temperature = run_payload.get("temperature") if isinstance(run_payload, dict) else None
    if not isinstance(temperature, (int, float)):
        temperature = 0.2

    max_tokens = run_payload.get("max_tokens", 512) if isinstance(run_payload, dict) else 512
    if not isinstance(max_tokens, int):
        max_tokens = 512

    return {
        "target": {
            "provider": "openai",
            "model": model_name,
        },
        "params": {
            "temperature": float(temperature),
            "max_tokens": max_tokens,
        },
    }


def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    client = _get_client()

    target = plan.get("target") or {}
    params = plan.get("params") or {}

    model = target.get("model") or "gpt-4o-mini"
    temperature = params.get("temperature", 0.2)
    max_tokens = params.get("max_tokens", 512)

    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful, concise assistant used inside AgenticLabs smart router.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    choice = resp.choices[0]
    output_text = choice.message.content or ""

    usage = getattr(resp, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

    cost_usd = _estimate_cost_usd(model, prompt_tokens, completion_tokens)

    provenance = {
        "provider": "openai",
        "model": model,
        "mode": "chat.completions",
        "input_tokens": int(prompt_tokens),
        "output_tokens": int(completion_tokens),
    }

    return {
        "output": output_text,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "confidence": 0.9,
        "provenance": provenance,
    }
