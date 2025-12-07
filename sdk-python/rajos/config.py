"""
Global configuration for the RAJOS SDK.
"""

from __future__ import annotations

from typing import Optional

BASE_URL: str = "http://localhost:8000"
API_KEY: Optional[str] = None
TIMEOUT: float = 5.0


def set_config(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
) -> None:
    global BASE_URL, API_KEY, TIMEOUT
    if base_url is not None:
        BASE_URL = base_url
    if api_key is not None:
        API_KEY = api_key
    if timeout is not None:
        TIMEOUT = timeout


__all__ = ["BASE_URL", "API_KEY", "TIMEOUT", "set_config"]
