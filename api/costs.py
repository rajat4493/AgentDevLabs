import json
import os
from pathlib import Path
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_pricing_profile():
    path_str = os.getenv(
        "AGENTICLABS_PRICING_PROFILE_PATH",
        "config/pricing_default.json",
    )
    path = Path(path_str)
    if not path.is_absolute():
        path = BASE_DIR / path
    with open(path, "r") as f:
        return json.load(f)


def get_unit_prices(provider: str, model: str):
    profile = load_pricing_profile()
    provider = (provider or "").lower()
    model = (model or "").lower()

    providers = profile.get("providers", {})
    table = providers.get(provider)
    if not table:
        return (0.0, 0.0)

    if model in table:
        p = table[model]
        return p["input_per_1k"], p["output_per_1k"]

    if "*" in table:
        p = table["*"]
        return p["input_per_1k"], p["output_per_1k"]

    return (0.0, 0.0)


def compute_costs(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    prompt_tokens = prompt_tokens or 0
    completion_tokens = completion_tokens or 0

    multiplier = float(os.getenv("AGENTICLABS_COST_MULTIPLIER", "1.0"))

    in_price, out_price = get_unit_prices(provider, model)
    actual_cost = (prompt_tokens * in_price + completion_tokens * out_price) / 1000.0
    actual_cost *= multiplier

    base_provider = os.getenv("AGENTICLABS_BASELINE_PROVIDER", "openai")
    base_model = os.getenv("AGENTICLABS_BASELINE_MODEL", "gpt-4o")
    base_in, base_out = get_unit_prices(base_provider, base_model)
    baseline_cost = (
        prompt_tokens * base_in + completion_tokens * base_out
    ) / 1000.0
    baseline_cost *= multiplier

    return actual_cost, baseline_cost


def compute_baseline_cost(prompt_tokens: int, completion_tokens: int = 0) -> float:
    """
    Compute the spend if all provided tokens ran on the configured baseline model.
    """
    prompt_tokens = prompt_tokens or 0
    completion_tokens = completion_tokens or 0

    multiplier = float(os.getenv("AGENTICLABS_COST_MULTIPLIER", "1.0"))
    base_provider = os.getenv("AGENTICLABS_BASELINE_PROVIDER", "openai")
    base_model = os.getenv("AGENTICLABS_BASELINE_MODEL", "gpt-4o")
    base_in, base_out = get_unit_prices(base_provider, base_model)

    baseline_cost = (prompt_tokens * base_in + completion_tokens * base_out) / 1000.0
    baseline_cost *= multiplier
    return baseline_cost
