from __future__ import annotations

from pathlib import Path

from backend.cost import PricingConfig, compute_costs


def test_compute_costs_from_config(tmp_path: Path) -> None:
    pricing_file = tmp_path / "pricing.json"
    pricing_file.write_text(
        """
        {
          "currency": "USD",
          "version": "test",
          "providers": {
            "stub": {
              "stub-1": {"input": 1.0, "output": 3.0, "unit": "per_1k"}
            }
          }
        }
        """,
        encoding="utf-8",
    )
    cfg = PricingConfig.from_file(pricing_file)
    breakdown = compute_costs(
        provider="stub",
        model="stub-1",
        input_tokens=500,
        output_tokens=1000,
        pricing_config=cfg,
    )
    assert breakdown.currency == "USD"
    assert breakdown.total_cost == round((0.5 * 0.001) + (1.0 * 0.003), 8)


def test_compute_costs_unknown_combo_defaults_to_zero() -> None:
    cfg = PricingConfig(
        {
            "currency": "USD",
            "providers": {"stub": {"stub-1": {"input": 1.0, "output": 1.0, "unit": "per_million"}}},
        }
    )
    breakdown = compute_costs(
        provider="missing",
        model="nope",
        input_tokens=123,
        output_tokens=456,
        pricing_config=cfg,
    )
    assert breakdown.total_cost == 0.0
    assert breakdown.input_tokens == 123
    assert breakdown.output_tokens == 456
