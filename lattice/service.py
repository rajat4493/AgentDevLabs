"""
Backward-compatible shim for legacy `lattice.service.complete` callers.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from .router.completion import route_completion
from .schemas import CompletionRequest

# Preserve the old type name for compatibility
CompleteRequest = CompletionRequest


def complete(request: CompleteRequest) -> Dict[str, Any]:
    """
    Synchronously execute the async router flow for older integrations.
    """

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        raise RuntimeError("complete() cannot be invoked from an active asyncio loop.")

    response = asyncio.run(route_completion(request))
    return response.model_dump()


__all__ = ["CompleteRequest", "complete"]
