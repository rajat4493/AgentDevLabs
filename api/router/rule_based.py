"""
Rule-based routing selector for provider + model decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

from .routing_rules import DEFAULT_ROUTING_RULES, SAFE_FALLBACK, load_routing_rules

RouteSource = Literal["rules_v1", "manual_override", "fallback"]


@dataclass
class SelectedModel:
    provider: str
    model: str
    band: str
    route_source: RouteSource


PROVIDER_DEFAULT_MODELS: Dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-opus-20240229",
    "gemini": "gemini-2.0-flash",
    "ollama": "qwen2:7b-instruct",
}

_BAND_MAP = {
    "simple": "low",
    "low": "low",
    "moderate": "medium",
    "medium": "medium",
    "complex": "high",
    "high": "high",
    "long_context": "high",
}


def _normalize_band(band: Optional[str]) -> str:
    if not band:
        return "medium"
    return _BAND_MAP.get(band.lower(), "medium")


def _normalize_task_type(task_type: Optional[str], rules: Dict[str, Dict[str, Dict[str, str]]]) -> str:
    if not task_type:
        return "default"
    tt = task_type.lower()
    if tt not in rules:
        return "default"
    return tt


def _pick_rule(task_rules: Dict[str, Dict[str, str]], band: str) -> Optional[Dict[str, str]]:
    if band in task_rules:
        return task_rules[band]
    if "medium" in task_rules:
        return task_rules["medium"]
    return next(iter(task_rules.values()), None) if task_rules else None


def _infer_provider_from_model(model: str, rules: Dict[str, Dict[str, Dict[str, str]]]) -> Optional[str]:
    target = model.lower()
    for bands in rules.values():
        for cfg in bands.values():
            if cfg.get("model", "").lower() == target:
                return cfg.get("provider")
    return None


def _find_model_for_provider(
    provider: str,
    rules: Dict[str, Dict[str, Dict[str, str]]],
    preferred_task: str,
    preferred_band: str,
) -> Optional[str]:
    task_rules = rules.get(preferred_task, {})
    band_cfg = task_rules.get(preferred_band)
    if band_cfg and band_cfg.get("provider") == provider:
        return band_cfg.get("model")
    for cfg in task_rules.values():
        if cfg.get("provider") == provider:
            return cfg.get("model")

    # Look across other task types for a reasonable default.
    for task_name, bands in rules.items():
        if task_name == preferred_task:
            continue
        for cfg in bands.values():
            if cfg.get("provider") == provider:
                return cfg.get("model")
    return PROVIDER_DEFAULT_MODELS.get(provider)


def select_model(
    *,
    band: str,
    task_type: Optional[str] = None,
    force_provider: Optional[str] = None,
    force_model: Optional[str] = None,
) -> SelectedModel:
    """
    Determine the provider/model selection for a request.
    """

    rules = load_routing_rules()
    band_key = _normalize_band(band)
    task_key = _normalize_task_type(task_type, rules)

    if force_model:
        provider = (force_provider or _infer_provider_from_model(force_model, rules) or "unknown").lower()
        return SelectedModel(provider=provider, model=force_model, band=band_key, route_source="manual_override")

    if force_provider:
        provider = force_provider.lower()
        model = _find_model_for_provider(provider, rules, task_key, band_key)
        if not model:
            model = PROVIDER_DEFAULT_MODELS.get(provider) or SAFE_FALLBACK["model"]
        return SelectedModel(provider=provider, model=model, band=band_key, route_source="manual_override")

    task_rules = rules.get(task_key) or DEFAULT_ROUTING_RULES.get(task_key, {})
    rule = _pick_rule(task_rules, band_key)
    if rule:
        provider = rule.get("provider") or SAFE_FALLBACK["provider"]
        model = rule.get("model") or PROVIDER_DEFAULT_MODELS.get(provider, SAFE_FALLBACK["model"])
        return SelectedModel(provider=provider, model=model, band=band_key, route_source="rules_v1")

    provider = SAFE_FALLBACK["provider"]
    model = SAFE_FALLBACK["model"]
    fallback_band = SAFE_FALLBACK.get("band", band_key)
    return SelectedModel(provider=provider, model=model, band=fallback_band, route_source="fallback")


__all__ = ["SelectedModel", "RouteSource", "PROVIDER_DEFAULT_MODELS", "select_model"]
