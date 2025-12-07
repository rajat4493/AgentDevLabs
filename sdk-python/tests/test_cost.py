from __future__ import annotations

from pathlib import Path

from rajos.cost import PricingConfig, compute_costs


def test_compute_costs_handles_pricing_file(tmp_path: Path) -> None:
    config_path = tmp_path / "pricing.json"
    config_path.write_text(
        """
        {
          "currency": "USD",
          "providers": {
            "stub": {
              "stub-echo": {"input": 1.0, "output": 2.0, "unit": "per_1k"}
            }
          }
        }
        """,
        encoding="utf-8",
    )
    cfg = PricingConfig.from_file(config_path)
    breakdown = compute_costs(
        provider="stub",
        model="stub-echo",
        input_tokens=1000,
        output_tokens=500,
        pricing_config=cfg,
    )
    assert breakdown.total_cost == round((1.0 / 1000) * 1000 + (2.0 / 1000) * 500, 8)


def test_compute_costs_unknown_model_zeroes_cost() -> None:
    cfg = PricingConfig({"currency": "USD", "providers": {}})
    breakdown = compute_costs(
        provider="missing",
        model="noop",
        input_tokens=5,
        output_tokens=10,
        pricing_config=cfg,
    )
    assert breakdown.total_cost == 0.0
    assert breakdown.input_tokens == 5
    assert breakdown.output_tokens == 10
