"""
RAJOS Python SDK surface.
"""

from .bands import get_bands_registry, select_model_for_band
from .client import ChatRouteResult, RajosClient
from .config import set_config as init
from .decorators import trace_llm_call, trace_span

__all__ = [
    "init",
    "RajosClient",
    "ChatRouteResult",
    "trace_llm_call",
    "trace_span",
    "get_bands_registry",
    "select_model_for_band",
]
