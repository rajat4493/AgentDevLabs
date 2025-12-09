"""
Custom error types and helpers for Lattice responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LatticeError(Exception):
    message: str
    provider: Optional[str] = None

    error_type: str = "internal_error"

    def __post_init__(self) -> None:
        super().__init__(self.message)


class ProviderTimeoutError(LatticeError):
    error_type = "provider_timeout"


class ProviderRateLimitError(LatticeError):
    error_type = "provider_rate_limit"


class ProviderValidationError(LatticeError):
    error_type = "provider_validation"


class ProviderInternalError(LatticeError):
    error_type = "provider_internal"


class ConfigurationError(LatticeError):
    error_type = "configuration"


class RateLimitExceededError(LatticeError):
    error_type = "rate_limit"


def error_response(exc: LatticeError) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": {
            "type": exc.error_type,
            "message": exc.message,
        }
    }
    if exc.provider:
        payload["error"]["provider"] = exc.provider
    return payload


__all__ = [
    "LatticeError",
    "ProviderTimeoutError",
    "ProviderRateLimitError",
    "ProviderValidationError",
    "ProviderInternalError",
    "ConfigurationError",
    "RateLimitExceededError",
    "error_response",
]
