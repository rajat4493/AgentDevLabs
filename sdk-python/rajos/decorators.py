"""
Decorator helpers for auto-tracing functions and manual spans.
"""

from __future__ import annotations

import functools
import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, MutableMapping, Optional, TypeVar

from .client import RajosClient, RajosClientError

F = TypeVar("F", bound=Callable[..., Any])
_global_client: Optional[RajosClient] = None


def get_global_client() -> RajosClient:
    global _global_client
    if _global_client is None:
        _global_client = RajosClient()
    return _global_client


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
        client_instance = client or get_global_client()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            call_metadata = kwargs.pop("rajos_metadata", None)
            prompt_text = _extract_prompt(args, kwargs)
            start_time = time.perf_counter()
            error: Exception | None = None
            result: Any = None
            status = "success"
            error_message: str | None = None
            raise_after_log: Exception | None = None

            try:
                result = func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                error = exc
                status = "error"
                error_message = repr(exc)
                result = None
                raise_after_log = exc
            finally:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                output_text = _format_output(result)
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
                    "status": status,
                    "error_message": error_message,
                }
                try:
                    client_instance.log_trace(**trace_payload)
                except RajosClientError as exc_log:
                    logging.getLogger("rajos.sdk").warning("Trace logging failed: %s", exc_log)

            if raise_after_log is not None:
                raise raise_after_log

        return wrapper  # type: ignore[return-value]

    return decorator


@contextmanager
def trace_span(
    operation: str,
    provider: str,
    model: str,
    framework: str = "raw",
    source: str = "sdk",
    extra: Optional[Dict[str, Any]] = None,
    client: Optional[RajosClient] = None,
):
    """
    Context manager for manually tracing LLM operations.
    """

    active_client = client or get_global_client()
    start = time.perf_counter()
    span_data: Dict[str, Any] = {"operation": operation, "extra": extra or {}}
    status = "success"
    error_message: str | None = None

    try:
        yield span_data
    except Exception as exc:  # noqa: BLE001
        status = "error"
        error_message = repr(exc)
        raise
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        input_text = span_data.get("input", "")
        output_text = span_data.get("output", "")
        try:
            active_client.log_trace(
                provider=provider,
                model=model,
                input=input_text,
                output=output_text,
                tokens=None,
                latency_ms=latency_ms,
                framework=framework,
                source=source,
                extra=span_data.get("extra"),
                status=status,
                error_message=error_message,
            )
        except RajosClientError as exc:
            logging.getLogger("rajos.sdk").warning("Trace span logging failed: %s", exc)
