"""
Core completion routing flow shared by the FastAPI surface and SDK.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from ..cache import CacheDisabled, get_cache, make_cache_key
from ..cloud import enqueue_cloud_ingest
from ..config import settings
from ..cost import compute_costs
from ..errors import (
    ConfigurationError,
    LatticeError,
    ProviderInternalError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from ..logging import configure_logger, log_event
from ..metrics import METRICS
from ..pii import detect_tags
from ..providers import PROVIDERS
from ..router import compute_alri_tag
from ..router.bands import BandsRegistry, get_bands_registry, find_provider_for_model
from ..schemas import (
    CompletionRequest,
    CompletionResponse,
    CostInfo,
    RoutingDecision,
    UsageStats,
)

logger = configure_logger("lattice.router.completion")

_BAND_ALIASES = {
    "simple": "low",
    "low": "low",
    "moderate": "mid",
    "mid": "mid",
    "medium": "mid",
    "complex": "high",
    "high": "high",
    "long_context": "high",
}


def _normalize_band(band: Optional[str]) -> Optional[str]:
    if not band:
        return None
    return _BAND_ALIASES.get(band.lower(), band.lower())


def _resolve_band(registry: BandsRegistry, requested_band: Optional[str]) -> str:
    if requested_band:
        band_cfg = registry.get_band(requested_band)
        if band_cfg:
            return band_cfg.name
    return registry.get_default_band().name


def _build_run_payload(req: CompletionRequest) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if req.metadata:
        payload.update(req.metadata)
    if req.max_tokens is not None:
        payload["max_tokens"] = req.max_tokens
    if req.temperature is not None:
        payload["temperature"] = req.temperature
    return payload


def _routing_reason(req: CompletionRequest, band: str) -> str:
    if req.model:
        return f"model override='{req.model}'"
    source = "user" if req.band else "auto"
    return f"band='{band}' ({source})"


def _maybe_enqueue_cloud_metadata(response: CompletionResponse) -> None:
    if not settings.cloud_ingest_key:
        return
    payload = {
        "provider": response.provider,
        "model": response.model,
        "band": response.band,
        "latency_ms": response.latency_ms,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "total_tokens": response.usage.total_tokens,
        "total_cost": response.cost.total_cost,
        "tags": list(response.tags),
        "timestamp": datetime.utcnow().isoformat(),
    }
    enqueue_cloud_ingest(payload)


async def route_completion(req: CompletionRequest) -> CompletionResponse:
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise ProviderValidationError("prompt is required")

    registry = get_bands_registry()
    resolved_band = _resolve_band(registry, _normalize_band(req.band))
    routing_reason = _routing_reason(req, resolved_band)

    prompt_tags = detect_tags(prompt)
    run_payload = _build_run_payload(req)

    cache_client = None
    try:
        cache_client = get_cache()
    except CacheDisabled:
        cache_client = None
    except Exception:
        cache_client = None
        logger.debug("cache_unavailable", exc_info=True)

    cache_checked = False
    cache_hit = False
    response: Optional[CompletionResponse] = None

    if req.model:
        provider_key = find_provider_for_model(req.model)
        if not provider_key:
            raise ProviderValidationError(
                f"Unknown model override '{req.model}'. Add it to the band config."
            )
        candidates: List[Dict[str, str]] = [{"provider": provider_key, "model": req.model}]
    else:
        band_cfg = registry.get_band(resolved_band) or registry.get_default_band()
        if not band_cfg.models:
            raise ConfigurationError(f"No providers configured for band '{band_cfg.name}'.")
        candidates = [{"provider": model.provider, "model": model.model} for model in band_cfg.models]

    routing_candidates = [dict(candidate) for candidate in candidates]
    last_error: Optional[LatticeError] = None

    for candidate in candidates:
        provider_key = candidate["provider"]
        model_name = candidate["model"]
        adapter = PROVIDERS.get(provider_key)
        if not adapter:
            raise ConfigurationError(f"Provider adapter '{provider_key}' not registered.")

        cache_key: Optional[str] = None
        cached_payload: Optional[Dict[str, Any]] = None
        if cache_client:
            cache_key = make_cache_key(prompt, provider_key, model_name, resolved_band)
            cache_checked = True
            try:
                cached_payload = cache_client.get(cache_key)
            except Exception:
                cached_payload = None

        if cached_payload:
            try:
                cached_response = CompletionResponse.model_validate(cached_payload)
            except ValidationError:
                cached_response = None

            if cached_response:
                cache_hit = True
                response_tags = detect_tags(cached_response.text)
                combined_tags = sorted(set(prompt_tags + response_tags + cached_response.tags))
                hydrated = cached_response.model_copy(update={"tags": combined_tags})
                METRICS.increment_cache_hit()
                METRICS.increment_requests(
                    provider=hydrated.provider,
                    model=hydrated.model,
                    band=hydrated.band or "auto",
                    latency_ms=hydrated.latency_ms,
                    input_tokens=hydrated.usage.input_tokens,
                    output_tokens=hydrated.usage.output_tokens,
                    total_cost=hydrated.cost.total_cost,
                    pii_tags_count=len(hydrated.tags),
                )
                log_event(
                    logger,
                    logging.INFO,
                    "completion_cache_hit",
                    provider=hydrated.provider,
                    model=hydrated.model,
                    band=hydrated.band,
                )
                _maybe_enqueue_cloud_metadata(hydrated)
                return hydrated

        try:
            plan = adapter.plan(run_payload, model_name)
            start = time.perf_counter()
            raw_result = adapter.execute(plan, prompt)
            measured_latency = (time.perf_counter() - start) * 1000.0
            latency_ms = float(raw_result.get("latency_ms") or measured_latency)
        except (ProviderTimeoutError, ProviderRateLimitError, ProviderInternalError) as exc:
            last_error = exc
            log_event(
                logger,
                logging.WARNING,
                "provider_failure",
                provider=provider_key,
                model=model_name,
                error_type=exc.error_type,
            )
            continue

        response_text = raw_result.get("output", "")
        prompt_tokens = int(raw_result.get("prompt_tokens") or 0)
        completion_tokens = int(raw_result.get("completion_tokens") or 0)
        total_tokens = prompt_tokens + completion_tokens

        cost_breakdown = compute_costs(
            provider=provider_key,
            model=model_name,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
        )
        usage = UsageStats(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        cost = CostInfo(**cost_breakdown.to_dict())

        response_tags = detect_tags(response_text)
        alri_tag = compute_alri_tag(resolved_band)
        tags = sorted(set(prompt_tags + response_tags + [alri_tag]))

        routing_decision = RoutingDecision(
            reason=routing_reason,
            candidates=routing_candidates,
            chosen={"provider": provider_key, "model": model_name},
        )

        response = CompletionResponse(
            text=response_text,
            provider=provider_key,
            model=model_name,
            band=resolved_band,
            latency_ms=latency_ms,
            usage=usage,
            cost=cost,
            tags=tags,
            routing=routing_decision,
        )

        if cache_client and cache_key:
            try:
                cache_client.set(cache_key, response.model_dump())
            except Exception:
                pass

        break

    if response is None:
        provider = getattr(last_error, "provider", None)
        raise ProviderInternalError("All provider candidates failed.", provider=provider)

    if cache_client and cache_checked and not cache_hit:
        METRICS.increment_cache_miss()

    METRICS.increment_requests(
        provider=response.provider,
        model=response.model,
        band=response.band or "auto",
        latency_ms=response.latency_ms,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        total_cost=response.cost.total_cost,
        pii_tags_count=len(response.tags),
    )
    log_event(
        logger,
        logging.INFO,
        "completion_success",
        provider=response.provider,
        model=response.model,
        band=response.band,
        latency_ms=int(response.latency_ms),
        cache="miss" if not cache_hit else "hit",
    )
    _maybe_enqueue_cloud_metadata(response)
    return response


__all__ = ["route_completion"]
