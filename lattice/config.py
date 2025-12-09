"""
Validated configuration for the Lattice backend.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:  # pragma: no cover - backwards compatibility
    from pydantic_settings import BaseSettings as _BaseSettings, SettingsConfigDict
    USE_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover
    SettingsConfigDict = ConfigDict  # type: ignore[assignment]
    USE_PYDANTIC_SETTINGS = False

    _DOTENV_VALUES: Dict[str, str] = {}

    def _load_env_file(path: Path) -> Dict[str, str]:
        data: Dict[str, str] = {}
        if not path.exists():
            return data
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
        return data

    _DOTENV_VALUES = _load_env_file(Path(".env"))

    class _BaseSettings(BaseModel):  # type: ignore[misc]
        model_config = ConfigDict(extra="ignore", populate_by_name=True)

        @classmethod
        def _collect_env(cls) -> Dict[str, str]:
            merged = {**_DOTENV_VALUES, **os.environ}
            values: Dict[str, str] = {}
            for field_name, field_info in cls.model_fields.items():
                alias = field_info.alias or field_name
                env_key = str(alias)
                if env_key in merged:
                    values[field_name] = merged[env_key]
            return values

        def __init__(self, **values):
            env_values = self._collect_env()
            env_values.update(values)
            super().__init__(**env_values)

from .errors import ConfigurationError

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


class Settings(_BaseSettings):
    """
    Configuration derived from environment variables with validation.
    """

    if USE_PYDANTIC_SETTINGS:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)
    else:  # pragma: no cover - pydantic fallback shim
        model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    environment: str = Field(default="dev", alias="LATTICE_ENV")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="LATTICE_CORS_ORIGINS")
    cache_disabled: bool = Field(default=False, alias="LATTICE_CACHE_DISABLED")
    cache_prefix: str = Field(default="lattice:cache", alias="LATTICE_CACHE_PREFIX")
    cache_ttl_seconds: int = Field(default=60, alias="LATTICE_CACHE_TTL_SECONDS")
    rate_limit_enabled: bool = Field(default=False, alias="LATTICE_RATE_LIMIT_ENABLED")
    rate_limit_per_day: int = Field(default=1000, alias="LATTICE_RATE_LIMIT_PER_DAY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    redis_url: Optional[str] = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    bands_config_path: str = Field(
        default=str(DEFAULT_DATA_DIR / "bands.json"),
        alias="BANDS_CONFIG_PATH",
    )
    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    ollama_url: str = Field(default="http://host.docker.internal:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="qwen2:7b-instruct", alias="OLLAMA_MODEL")
    anthropic_system_prompt: str = Field(
        default="You are a concise, high-signal assistant for lattice routed requests.",
        alias="ANTHROPIC_SYSTEM_PROMPT",
    )
    pricing_file: str = Field(
        default=str(DEFAULT_DATA_DIR / "pricing.json"),
        alias="LATTICE_PRICING_FILE",
    )
    routing_rules_path: str = Field(
        default=str(DEFAULT_DATA_DIR / "routing_rules.json"),
        alias="LATTICE_ROUTING_RULES_PATH",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | List[str] | None) -> List[str]:
        if value is None:
            return ["http://localhost:3000"]
        if isinstance(value, str):
            items = [origin.strip() for origin in value.split(",") if origin.strip()]
            return items or ["http://localhost:3000"]
        return value

    @model_validator(mode="after")
    def validate_provider_keys(self):
        env = (self.environment or "dev").lower()
        if env in {"prod", "cloud"} and not (self.openai_api_key or self.anthropic_api_key):
            raise ConfigurationError(
                "At least one provider API key must be configured for production environments."
            )
        bands_path = Path(self.bands_config_path)
        if not bands_path.exists():
            raise ConfigurationError(f"Bands configuration not found: {bands_path}")
        pricing_path = Path(self.pricing_file)
        if not pricing_path.exists():
            raise ConfigurationError(f"Pricing configuration not found: {pricing_path}")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
