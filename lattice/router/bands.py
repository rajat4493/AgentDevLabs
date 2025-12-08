"""
Band configuration helpers for routing decisions.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BandModel:
    provider: str
    model: str


@dataclass
class BandConfig:
    name: str
    description: str
    models: List[BandModel]


class BandsRegistry:
    """
    Loads and manages band -> model mapping.
    """

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._raw = raw or {}
        self.version: Optional[str] = self._raw.get("version")
        self.default_band: str = self._raw.get("default_band", "mid")
        self._bands: Dict[str, BandConfig] = {}

        bands_raw = self._raw.get("bands", {})
        for band_name, band_cfg in bands_raw.items():
            models: List[BandModel] = []
            for model_cfg in band_cfg.get("models", []):
                if not model_cfg:
                    continue
                models.append(
                    BandModel(
                        provider=str(model_cfg.get("provider", "")).lower(),
                        model=str(model_cfg.get("model", "")),
                    )
                )
            self._bands[band_name] = BandConfig(
                name=band_name,
                description=band_cfg.get("description", ""),
                models=models,
            )

    @classmethod
    def from_file(cls, path: str | Path) -> "BandsRegistry":
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Bands config not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls(raw)

    def get_band(self, band: str) -> Optional[BandConfig]:
        return self._bands.get(band)

    def get_default_band(self) -> BandConfig:
        return self._bands.get(self.default_band) or next(iter(self._bands.values()))

    def list_bands(self) -> List[str]:
        return list(self._bands.keys())

    def find_provider_for_model(self, model: str) -> Optional[str]:
        target = model.lower()
        for band in self._bands.values():
            for candidate in band.models:
                if candidate.model.lower() == target:
                    return candidate.provider
        return None


_BANDS_REGISTRY: Optional[BandsRegistry] = None


def get_bands_registry() -> BandsRegistry:
    global _BANDS_REGISTRY
    if _BANDS_REGISTRY is not None:
        return _BANDS_REGISTRY

    default_path = Path(__file__).parent.parent / "data" / "bands.json"
    path_str = os.getenv("LATTICE_BANDS_FILE", str(default_path))
    _BANDS_REGISTRY = BandsRegistry.from_file(path_str)
    return _BANDS_REGISTRY


def select_model_for_band(
    *,
    band: Optional[str],
    explicit_provider: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Select a provider/model tuple for the supplied band.

    Returns (provider, model, routing_reason).
    """

    registry = get_bands_registry()

    if band:
        band_cfg = registry.get_band(band) or registry.get_default_band()
        routing_band = band_cfg.name
    else:
        band_cfg = registry.get_default_band()
        routing_band = band_cfg.name

    candidates: List[BandModel] = list(band_cfg.models)
    if not candidates:
        raise ValueError(f"No models configured for band '{routing_band}'.")

    if explicit_provider:
        target = explicit_provider.lower()
        filtered = [model for model in candidates if model.provider == target]
        if not filtered:
            raise ValueError(
                f"No models available for band '{routing_band}' with provider '{explicit_provider}'."
            )
        candidates = filtered

    chosen = random.choice(candidates)
    reason = f"band:{routing_band}"
    return chosen.provider, chosen.model, reason


def find_provider_for_model(model: str) -> Optional[str]:
    registry = get_bands_registry()
    return registry.find_provider_for_model(model)


__all__ = ["BandModel", "BandConfig", "BandsRegistry", "get_bands_registry", "select_model_for_band", "find_provider_for_model"]
