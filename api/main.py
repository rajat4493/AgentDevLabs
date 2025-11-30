import time
from decimal import Decimal
from typing import Iterable, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from shared.models import (
    AuditInfo,
    MetricsInfo,
    RunRequest,
    RunResponse,
    Provenance,
    PolicyEvaluation,
)
from router import compute_alri_tag, evaluate_policy, new_run_id
from router.complexity import choose_band, score_complexity
from router.rule_based import PROVIDER_DEFAULT_MODELS, SelectedModel, select_model
from router.routing_rules import load_routing_rules
from router.model_registry import NAIVE_BASELINE_MODEL_KEY
from router.routing_bands import RoutingBand
from logger import log_event
from providers import PROVIDERS
from costs import compute_costs
from governance.alri import compute_alri_v2
from routes import logs, metrics
from db.models import Base
from db.router_runs_repo import get_summary, list_runs as list_runs_repo, log_run
from db.session import engine, get_db
from config.router import RouterMode
from config.model_registry import MODEL_REGISTRY
from cost.calculator import calculate_cost, resolve_model_key
from deps import get_router_mode_dep, get_tenant_dep
from models.tenant import (
    AutonomyLevel,
    DataSensitivity,
    Tenant,
    TenantBand,
    TenantRegion,
    TenantStatus,
)
from routing.categories import classify_query, QueryCategory
from routing.scoring import choose_enhanced_model
from pricing import estimate_cost_for_model
from shared.tenants import TenantRead, TenantSettingsUpdate

app = FastAPI(title="AgenticLabs API", version="0.1.2")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router)
app.include_router(metrics.router)

DEFAULT_MAX_OUTPUT_TOKENS = 512
BAND_ORDER: List[str] = ["low", "medium", "high", "premium"]


def estimate_prompt_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def cap_band_for_tenant(band: str, max_band: TenantBand) -> str:
    try:
        band_idx = BAND_ORDER.index(band)
    except ValueError:
        band_idx = BAND_ORDER.index("medium")
    try:
        limit_idx = BAND_ORDER.index(max_band.value.lower())
    except ValueError:
        limit_idx = BAND_ORDER.index("high")
    if band_idx > limit_idx:
        return BAND_ORDER[limit_idx]
    return band


def ensure_request_limits(tenant: Tenant, estimated_tokens: int) -> None:
    # TODO: integrate per-tenant daily counters as soon as usage table ships.
    if estimated_tokens > tenant.max_tokens_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request exceeds tenant max tokens ({tenant.max_tokens_per_request})",
        )


def ensure_credit_limit(tenant: Tenant, estimated_cost: float) -> None:
    usage = Decimal(str(tenant.usage_usd or 0))
    credit_limit = Decimal(str(tenant.credit_limit_usd or 0))
    if usage + Decimal(str(estimated_cost)) > credit_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Credit limit exceeded",
        )


def compute_risk_score(tenant: Tenant) -> int:
    sensitivity = tenant.default_data_sensitivity
    autonomy = tenant.default_autonomy_level
    if sensitivity == DataSensitivity.PUBLIC:
        return 0
    if sensitivity == DataSensitivity.INTERNAL:
        return 1
    if sensitivity == DataSensitivity.PII:
        return 2 if autonomy == AutonomyLevel.ANSWER_ONLY else 3
    return 0


def filter_governance_providers(
    providers: List[str], tenant: Tenant, risk_score: int
) -> tuple[List[str], List[str]]:
    filtered = providers[:]
    blocked: List[str] = []
    if (
        tenant.region == TenantRegion.EU
        and tenant.default_data_sensitivity == DataSensitivity.PII
    ):
        if "gemini" in filtered:
            filtered = [p for p in filtered if p != "gemini"]
            blocked.append("gemini")
    return filtered, blocked


def allowed_model_keys_for_tenant(
    tenant: Tenant, provider_whitelist: Iterable[str] | None = None
) -> List[str]:
    source = provider_whitelist if provider_whitelist is not None else (tenant.allowed_providers or [])
    providers = [p.lower() for p in source]
    if not providers:
        providers = ["openai"]
    keys = [
        key
        for key, cfg in MODEL_REGISTRY.items()
        if cfg.provider in providers
    ]
    return keys


@app.get("/v1/metrics/summary")
def metrics_summary(db: Session = Depends(get_db)):
    """
    Aggregate router metrics for the dashboard.
    """
    summary = get_summary(db)
    return JSONResponse(summary)

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "agenticlabs-api",
        "routing_rules": load_routing_rules(),
    }


@app.get("/debug/tenant", response_model=TenantRead)
def debug_tenant(tenant: Tenant = Depends(get_tenant_dep)):
    return TenantRead.from_orm(tenant)


@app.get("/tenant/settings", response_model=TenantRead)
def read_tenant_settings(tenant: Tenant = Depends(get_tenant_dep)):
    return TenantRead.from_orm(tenant)


@app.patch("/tenant/settings", response_model=TenantRead)
def update_tenant_settings(
    payload: TenantSettingsUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant_dep),
):
    updated = False
    if payload.default_data_sensitivity is not None:
        tenant.default_data_sensitivity = payload.default_data_sensitivity
        updated = True
    if payload.default_autonomy_level is not None:
        tenant.default_autonomy_level = payload.default_autonomy_level
        updated = True

    if updated:
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    return TenantRead.from_orm(tenant)

@app.post("/v1/run", response_model=RunResponse)
def run_endpoint(
    payload: RunRequest,
    db: Session = Depends(get_db),
    router_mode: RouterMode = Depends(get_router_mode_dep),
    tenant: Tenant = Depends(get_tenant_dep),
):
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is suspended",
        )
    if payload.router_mode:
        try:
            router_mode = RouterMode(payload.router_mode.lower())
        except ValueError:
            router_mode = router_mode
    rid = new_run_id()
    t_start = time.perf_counter()
    log_event(
        "router_in",
        {"run_id": rid, "agent_id": payload.agent_id, "router_mode": router_mode.value},
    )

    # ---- Smart routing (with manual override) ----
    cscore = score_complexity(payload.prompt)
    inferred_band_raw = choose_band(cscore, payload.prompt)
    inferred_band = cap_band_for_tenant(
        RoutingBand.normalize(inferred_band_raw).value,
        tenant.max_band,
    )

    overrides = payload.policy_overrides or {}
    force_model = payload.force_model or overrides.get("force_model")
    force_provider = payload.force_provider or overrides.get("force_provider")
    force_band = payload.force_band or overrides.get("force_band")

    def canonical_band(value: str | None) -> str:
        return cap_band_for_tenant(
            RoutingBand.normalize(value).value,
            tenant.max_band,
        )

    requested_band = canonical_band(payload.band or inferred_band)
    if isinstance(force_band, str) and force_band:
        requested_band = canonical_band(force_band)

    task_type = payload.task_type
    estimated_prompt_tokens = estimate_prompt_tokens(payload.prompt)
    estimated_total_tokens = estimated_prompt_tokens + DEFAULT_MAX_OUTPUT_TOKENS
    ensure_request_limits(tenant, estimated_total_tokens)
    risk_score = compute_risk_score(tenant)
    configured_providers = [p.lower() for p in (tenant.allowed_providers or [])] or [
        "openai"
    ]
    allowed_providers, blocked_providers = filter_governance_providers(
        configured_providers, tenant, risk_score
    )
    if not allowed_providers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No providers available for this tenant based on policies",
        )
    allowed_model_keys = allowed_model_keys_for_tenant(
        tenant, allowed_providers
    )
    if not allowed_model_keys:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No models available for this tenant",
        )

    if force_provider and force_provider.lower() not in allowed_providers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider not allowed for tenant",
        )

    default_selection: SelectedModel = select_model(
        band=inferred_band,
        task_type=task_type,
    )

    selected: SelectedModel = select_model(
        band=requested_band,
        task_type=task_type,
        force_provider=force_provider,
        force_model=force_model,
    )
    category, category_conf = classify_query(payload.prompt)

    provider_name = selected.provider
    model_name = selected.model
    resolved_band = selected.band
    selection_source = selected.route_source

    if selected.provider not in allowed_providers:
        fallback_provider = allowed_providers[0]
        selected = select_model(
            band=selected.band,
            task_type=task_type,
            force_provider=fallback_provider,
        )

    allowed_keys = [
        key for key in allowed_model_keys if MODEL_REGISTRY[key].provider in allowed_providers
    ] or allowed_model_keys

    if router_mode == RouterMode.ENHANCED:
        choice = choose_enhanced_model(
            category=category,
            allowed_model_keys=allowed_keys,
            resolved_band=resolved_band,
            cost_mode=tenant.cost_mode.value if hasattr(tenant.cost_mode, "value") else tenant.cost_mode,
        )
        if choice:
            provider_name = choice.provider
            model_name = choice.model_id
            selection_source = "enhanced"

    final_key = f"{provider_name}:{model_name}"
    if allowed_keys and final_key not in allowed_keys:
        fallback_choice = choose_enhanced_model(
            category=category,
            allowed_model_keys=allowed_keys,
            resolved_band=resolved_band,
            cost_mode=tenant.cost_mode.value if hasattr(tenant.cost_mode, "value") else tenant.cost_mode,
        )
        if fallback_choice:
            provider_name = fallback_choice.provider
            model_name = fallback_choice.model_id
            selection_source = "enhanced"

    model_key = resolve_model_key(provider_name, model_name) or final_key
    estimated_upper_cost = calculate_cost(
        model_key=model_key,
        provider=provider_name,
        model=model_name,
        input_tokens=estimated_prompt_tokens,
        output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
    )
    ensure_credit_limit(tenant, estimated_upper_cost)

    if provider_name not in PROVIDERS:
        provider_name = "openai"
        model_name = PROVIDER_DEFAULT_MODELS.get(provider_name, model_name)

    provider_impl = PROVIDERS.get(provider_name)
    if provider_impl is None:
        raise ValueError(f"Provider '{provider_name}' is not configured")

    governance_info = {
        "risk_score": risk_score,
        "region": tenant.region.value if hasattr(tenant.region, "value") else tenant.region,
        "default_data_sensitivity": tenant.default_data_sensitivity.value
        if hasattr(tenant.default_data_sensitivity, "value")
        else tenant.default_data_sensitivity,
        "default_autonomy_level": tenant.default_autonomy_level.value
        if hasattr(tenant.default_autonomy_level, "value")
        else tenant.default_autonomy_level,
        "blocked_providers": blocked_providers,
    }

    log_event("route_complexity", {
        "run_id": rid,
        "score": round(cscore, 3),
        "band": resolved_band,
        "inferred_band": inferred_band,
        "provider": provider_name,
        "model": model_name,
        "force_model": bool(force_model),
        "force_band": bool(force_band),
        "force_provider": bool(force_provider),
        "route_source": selection_source,
        "category": category.value,
        "category_confidence": category_conf,
        "risk_score": risk_score,
        "blocked_providers": blocked_providers,
    })

    # ---- Plan + Execute ----
    plan = provider_impl.plan(payload.model_dump(), model_name=model_name)
    log_event("route_plan", {"run_id": rid, "plan": plan})
    t_router_done = time.perf_counter()

    t_provider_start = time.perf_counter()
    result = provider_impl.execute(plan, payload.prompt)
    t_provider_end = time.perf_counter()

    prompt_tokens = result.get("prompt_tokens")
    if prompt_tokens is None:
        prompt_tokens = (result.get("provenance") or {}).get("input_tokens", 0)
    completion_tokens = result.get("completion_tokens")
    if completion_tokens is None:
        completion_tokens = (result.get("provenance") or {}).get("output_tokens", 0)

    prompt_tokens = int(prompt_tokens or 0)
    completion_tokens = int(completion_tokens or 0)

    model_key = resolve_model_key(provider_name, model_name) or f"{provider_name}:{model_name}"
    cost_usd = calculate_cost(
        model_key=model_key,
        provider=provider_name,
        model=model_name,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    if cost_usd <= 0:
        legacy_cost, _ = compute_costs(
            provider=provider_name,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        if legacy_cost and legacy_cost > 0:
            cost_usd = legacy_cost
        else:
            cost_usd = float(result.get("cost_usd", 0.0) or 0.0)

    baseline_cost = calculate_cost(
        model_key=NAIVE_BASELINE_MODEL_KEY,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    if baseline_cost <= 0:
        _, legacy_baseline = compute_costs(
            provider=provider_name,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        baseline_cost = legacy_baseline or cost_usd
    cost_usd = float(cost_usd or 0.0)
    baseline_cost = float(baseline_cost or cost_usd)

    result["cost_usd"] = cost_usd

    log_event("provider_out", {
        "run_id": rid,
        "latency_ms": result["latency_ms"],
        "cost_usd": cost_usd,
    })

    # ---- Policy evaluation ----
    threshold = 0.7
    if payload.policy_overrides and isinstance(payload.policy_overrides.get("confidence_threshold"), (int, float)):
        threshold = float(payload.policy_overrides["confidence_threshold"])
    pol = evaluate_policy(result["confidence"], threshold)

    # ---- ALRI tag ----
    ctx = payload.context or {}
    alri_tag = compute_alri_tag(ctx.get("risk_band"), ctx.get("jurisdiction"))

    # ---- Metrics ----
    overrides_used = selected.route_source == "manual_override"

    run_status = "ok" if not pol["hil_triggered"] else "hil_required"

    alri_score, alri_tier = compute_alri_v2(
        band=selected.band,
        provider=provider_name,
        model=model_name,
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        cost_usd=result["cost_usd"],
        baseline_cost_usd=baseline_cost,
        overrides_used=overrides_used,
        prompt_text=payload.prompt,
    )

    t_done = time.perf_counter()
    total_latency_ms = (t_done - t_start) * 1000.0
    router_latency_ms = (t_router_done - t_start) * 1000.0
    provider_latency_ms = (t_provider_end - t_provider_start) * 1000.0
    processing_latency_ms = max(
        0.0, total_latency_ms - router_latency_ms - provider_latency_ms
    )

    # Routing efficiency: compare against default selection cost
    default_model_key = resolve_model_key(
        default_selection.provider, default_selection.model
    ) or f"{default_selection.provider}:{default_selection.model}"
    default_cost = calculate_cost(
        model_key=default_model_key,
        provider=default_selection.provider,
        model=default_selection.model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    if default_cost <= 0:
        legacy_default_cost, _ = compute_costs(
            provider=default_selection.provider,
            model=default_selection.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        default_cost = legacy_default_cost
    default_cost = float(default_cost or 0.0)
    epsilon = 0.02
    routing_efficient = False
    if default_cost > 0:
        routing_efficient = cost_usd <= (default_cost * (1 + epsilon))
    else:
        routing_efficient = True

    what_if_cost_usd = estimate_cost_for_model(
        "gpt-4.1",
        prompt_tokens,
        category,
    )

    log_run(
        db,
        tenant_id=str(tenant.id),
        band=resolved_band,
        provider=provider_name,
        model=model_name,
        latency_ms=total_latency_ms,
        router_latency_ms=router_latency_ms,
        provider_latency_ms=provider_latency_ms,
        processing_latency_ms=processing_latency_ms,
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        cost_usd=result["cost_usd"],
        baseline_cost_usd=baseline_cost,
        alri_score=alri_score,
        alri_tier=alri_tier,
        status=run_status,
        routing_efficient=routing_efficient,
        query_category=category.value,
        query_category_conf=category_conf,
        counterfactual_cost_usd=what_if_cost_usd,
    )

    tenant.usage_usd = (
        Decimal(str(tenant.usage_usd or 0)) + Decimal(str(cost_usd or 0))
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # ---- Response ----
    provenance = result.get("provenance") or {}
    provenance.update(
        {
            "provider": provider_name,
            "model": model_name,
            "route_source": selection_source,
        }
    )
    provenance["governance"] = governance_info
    result["provenance"] = provenance

    resp = RunResponse(
        run_id=rid,
        status=run_status,
        output=result["output"],
        confidence=result["confidence"],
        provenance=Provenance(**result["provenance"]),
        policy_evaluation=PolicyEvaluation(**pol),
        metrics=MetricsInfo(latency_ms=int(total_latency_ms), cost_usd=result["cost_usd"]),
        audit=AuditInfo(retention_class=alri_tag, audit_hash=None),
        query_category=category.value,
        query_category_conf=category_conf,
    )

    log_event("router_out", {"run_id": rid, "status": resp.status})
    return JSONResponse(resp.model_dump())
