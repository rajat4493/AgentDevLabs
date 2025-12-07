from __future__ import annotations

from pathlib import Path

from rajos.bands import BandsRegistry, select_model_for_band, find_provider_for_model


def _write_config(tmp_path: Path) -> Path:
    config = tmp_path / "bands.json"
    config.write_text(
        """
        {
          "default_band": "mid",
          "bands": {
            "low": {
              "models": [{"provider": "stub", "model": "stub-low"}]
            },
            "mid": {
              "models": [
                {"provider": "stub", "model": "stub-mid"},
                {"provider": "other", "model": "other-mid"}
              ]
            }
          }
        }
        """,
        encoding="utf-8",
    )
    return config


def test_registry_loads_bands(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    registry = BandsRegistry.from_file(config_path)
    assert registry.get_default_band().name == "mid"
    assert "low" in registry.list_bands()
    assert registry.find_provider_for_model("other-mid") == "other"


def test_select_model_for_band_filters_provider(tmp_path: Path, monkeypatch) -> None:
    config_path = _write_config(tmp_path)
    monkeypatch.setenv("RAJOS_BANDS_FILE", str(config_path))
    provider, model, reason = select_model_for_band(band="mid", explicit_provider="other")
    assert provider == "other"
    assert model == "other-mid"
    assert reason.startswith("band:")


def test_find_provider_for_missing_model(tmp_path: Path, monkeypatch) -> None:
    config_path = _write_config(tmp_path)
    monkeypatch.setenv("RAJOS_BANDS_FILE", str(config_path))
    assert find_provider_for_model("missing") is None
