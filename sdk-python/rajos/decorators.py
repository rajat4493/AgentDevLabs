"""
Decorator helpers for auto-tracing functions.
"""

from __future__ import annotations

import functools
import json
import time
from typing import Any, Callable, Dict, MutableMapping, Optional, TypeVar

from .client import RajosClient, RajosClientError

F = TypeVar("F", bound=Callable[..., Any])


def _extract_prompt(args: tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    prompt = kwargs.get("prompt")
    if isinstance(prompt, str):
        return prompt
    for value in args:
        if isinstance(value, str):
            return value
    return ""


def _format_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def trace_llm_call(
    *,
    provider: str,
    model: str,
    framework: str = "python-sdk",
    source: str = "sdk",
    client: RajosClient | None = None,
    extra: Optional[MutableMapping[str, Any]] = None,
) -> Callable[[F], F]:
    """
    Instrument a function so every invocation is recorded as a RAJOS trace.

    Pass `rajos_metadata` as a keyword argument when calling the wrapped function
    to attach per-call metadata to the trace.
    """

    base_extra = dict(extra or {})

    def decorator(func: F) -> F:
        client_instance = client or RajosClient()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            call_metadata = kwargs.pop("rajos_metadata", None)
            prompt_text = _extract_prompt(args, kwargs)
            start_time = time.perf_counter()
            error: Exception | None = None
            result: Any = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as exc:
                error = exc
                raise
            finally:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                output_text = _format_output(result) if error is None else f"Exception: {error}"
                extra_payload: Dict[str, Any] = {"decorator": {"function": func.__qualname__}}
                extra_payload.update(base_extra)
                if isinstance(call_metadata, MutableMapping):
                    extra_payload.update(call_metadata)
                trace_payload = {
                    "provider": provider,
                    "model": model,
                    "input": prompt_text,
                    "output": output_text,
                    "latency_ms": duration_ms,
                    "tokens": None,
                    "framework": framework,
                    "source": source,
                    "extra": extra_payload or None,
                }
                try:
                    client_instance.create_trace(**trace_payload)
                except RajosClientError:
                    # Fail open: the SDK should never crash user code due to tracing.
                    pass

        return wrapper  # type: ignore[return-value]

    return decorator
