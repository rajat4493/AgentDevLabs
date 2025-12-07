"""
Cost layer utilities shipped with the RAJOS SDK.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Literal, Optional

TokenUnit = Literal["per_million", "per_1k"]


@dataclass
class CostBreakdown:
    """Represents cost of a single LLM call."""

    currency: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    pricing_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PricingConfig:
    """Thin wrapper around a pricing JSON definition."""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._raw = raw or {}
        self._providers: Dict[str, Any] = self._raw.get("providers", {})
        self.currency: str = self._raw.get("currency", "USD")
        self.version: Optional[str] = self._raw.get("version")

    @classmethod
    def from_file(cls, path: str | Path) -> "PricingConfig":
        pricing_path = Path(path)
        if not pricing_path.exists():
            raise FileNotFoundError(f"Pricing file not found: {pricing_path}")

        with pricing_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls(raw)

    def get_model_pricing(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        provider_cfg = self._providers.get(provider)
        if not provider_cfg:
            return None
        return provider_cfg.get(model)


_PRICING_CONFIG: Optional[PricingConfig] = None


def get_pricing_config() -> PricingConfig:
    """
    Lazily load pricing config.

    Override the path via RAJOS_PRICING_FILE env var.
    """

    global _PRICING_CONFIG
    if _PRICING_CONFIG is not None:
        return _PRICING_CONFIG

    default_path = Path(__file__).parent / "data" / "pricing.json"
    path_str = os.getenv("RAJOS_PRICING_FILE", str(default_path))
    _PRICING_CONFIG = PricingConfig.from_file(path_str)
    return _PRICING_CONFIG


def _normalize_unit_price(raw_price: float, unit: TokenUnit) -> float:
    """
    Convert "price per unit" to "price per single token".

    - per_million -> price / 1_000_000
    - per_1k      -> price / 1_000
    """

    if unit == "per_million":
        return raw_price / 1_000_000.0
    if unit == "per_1k":
        return raw_price / 1_000.0
    return raw_price


def compute_costs(
    *,
    provider: str,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    pricing_config: Optional[PricingConfig] = None,
) -> CostBreakdown:
    """
    Core cost calculation helper.

    Unknown provider/model combos produce a zeroed breakdown but still track tokens.
    """

    cfg = pricing_config or get_pricing_config()
    pricing = cfg.get_model_pricing(provider, model)

    in_tokens = int(input_tokens or 0)
    out_tokens = int(output_tokens or 0)

    if not pricing:
        return CostBreakdown(
            currency=cfg.currency,
            provider=provider,
            model=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
            pricing_version=cfg.version,
        )

    unit: TokenUnit = pricing.get("unit", "per_million")  # type: ignore[assignment]
    input_price_raw = float(pricing.get("input", 0.0))
    output_price_raw = float(pricing.get("output", 0.0))

    input_price_per_token = _normalize_unit_price(input_price_raw, unit)
    output_price_per_token = _normalize_unit_price(output_price_raw, unit)

    input_cost = in_tokens * input_price_per_token
    output_cost = out_tokens * output_price_per_token
    total_cost = input_cost + output_cost

    return CostBreakdown(
        currency=cfg.currency,
        provider=provider,
        model=model,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        input_cost=round(input_cost, 8),
        output_cost=round(output_cost, 8),
        total_cost=round(total_cost, 8),
        pricing_version=cfg.version,
    )


__all__ = ["CostBreakdown", "PricingConfig", "compute_costs", "get_pricing_config"]
