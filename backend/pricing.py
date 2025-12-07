from __future__ import annotations

from backend.cost import compute_costs, get_pricing_config, CostBreakdown


def get_pricing(model: str, default: str = "gpt-4o-mini") -> dict:
    """
    Backwards compatible helper that returns pricing info for a model.
    """

    cfg = get_pricing_config()
    provider_pricing = cfg._providers.get("openai") or {}
    pricing = provider_pricing.get(model) or provider_pricing.get(default)
    return pricing or {"input": 0.0, "output": 0.0, "unit": "per_million"}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    breakdown = compute_costs(
        provider="openai",
        model=model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    return breakdown.total_cost


def calc_baseline_cost(
    prompt_tokens: int,
    completion_tokens: int,
    baseline_model: str = "gpt-4o",
) -> float:
    breakdown = compute_costs(
        provider="openai",
        model=baseline_model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    return breakdown.total_cost


__all__ = ["CostBreakdown", "get_pricing_config", "get_pricing", "estimate_cost", "calc_baseline_cost"]
