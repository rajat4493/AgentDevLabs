"""
Routing rules configuration with safe defaults.

Rules map a task_type ("default", "code", etc.) and a band ("low", "medium", "high")
to a provider/model combination.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Mapping, MutableMapping

RoutingRules = Dict[str, Dict[str, Dict[str, str]]]

DEFAULT_ROUTING_RULES: RoutingRules = {
    "default": {
        "low": {"provider": "openai", "model": "gpt-4o-mini"},
        "medium": {"provider": "openai", "model": "gpt-4o"},
        "high": {"provider": "anthropic", "model": "claude-3-opus-20240229"},
    },
    "code": {
        "low": {"provider": "ollama", "model": "qwen2:7b-instruct"},
        "medium": {"provider": "openai", "model": "gpt-4o"},
        "high": {"provider": "openai", "model": "gpt-4o"},
    },
}

SAFE_FALLBACK = {"provider": "openai", "model": "gpt-4o-mini", "band": "medium"}


def _default_config_path() -> Path:
    env_path = os.getenv("LATTICE_ROUTING_RULES_PATH")
    if env_path:
        return Path(env_path)
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "config" / "routing_rules.json"


def _load_rules_from_file(path: Path) -> RoutingRules:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, MutableMapping):
                # Basic sanitization: only keep dict -> dict -> dict[str, str]
                cleaned: RoutingRules = {}
                for task_type, bands in data.items():
                    if not isinstance(bands, Mapping):
                        continue
                    cleaned_bands: Dict[str, Dict[str, str]] = {}
                    for band, cfg in bands.items():
                        if not isinstance(cfg, Mapping):
                            continue
                        provider = str(cfg.get("provider", "")).strip()
                        model = str(cfg.get("model", "")).strip()
                        if provider and model:
                            cleaned_bands[band.lower()] = {
                                "provider": provider.lower(),
                                "model": model,
                            }
                    if cleaned_bands:
                        cleaned[task_type.lower()] = cleaned_bands
                return cleaned
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


@lru_cache(maxsize=1)
def load_routing_rules() -> RoutingRules:
    """
    Load routing rules from disk, falling back to DEFAULT_ROUTING_RULES when absent.
    """
    path = _default_config_path()
    loaded = _load_rules_from_file(path)
    if not loaded:
        return DEFAULT_ROUTING_RULES

    # Merge with defaults to ensure required keys exist.
    merged: RoutingRules = {}
    defaults = DEFAULT_ROUTING_RULES.copy()
    merged.update(defaults)
    for task_type, bands in loaded.items():
        if task_type not in merged:
            merged[task_type] = {}
        merged[task_type].update(bands)
    return merged


__all__ = ["RoutingRules", "SAFE_FALLBACK", "DEFAULT_ROUTING_RULES", "load_routing_rules"]
