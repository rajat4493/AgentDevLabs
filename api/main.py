import time
from fastapi import Depends, FastAPI
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
from logger import log_event
from providers import PROVIDERS
from costs import compute_costs
from governance.alri import compute_alri_v2
from routes import logs
from db.models import Base
from db.router_runs_repo import get_summary, list_runs as list_runs_repo, log_run
from db.session import engine, get_db

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

@app.post("/v1/run", response_model=RunResponse)
def run_endpoint(payload: RunRequest, db: Session = Depends(get_db)):
    rid = new_run_id()
    t_start = time.perf_counter()
    log_event("router_in", {"run_id": rid, "agent_id": payload.agent_id})

    # ---- Smart routing (with manual override) ----
    cscore = score_complexity(payload.prompt)
    inferred_band = choose_band(cscore, payload.prompt)

    overrides = payload.policy_overrides or {}
    force_model = payload.force_model or overrides.get("force_model")
    force_provider = payload.force_provider or overrides.get("force_provider")
    force_band = payload.force_band or overrides.get("force_band")

    requested_band = payload.band or inferred_band
    if isinstance(force_band, str) and force_band:
        requested_band = force_band

    task_type = payload.task_type

    selected: SelectedModel = select_model(
        band=requested_band,
        task_type=task_type,
        force_provider=force_provider,
        force_model=force_model,
    )

    provider_name = selected.provider
    model_name = selected.model
    resolved_band = selected.band

    if provider_name not in PROVIDERS:
        provider_name = "openai"
        model_name = PROVIDER_DEFAULT_MODELS.get(provider_name, model_name)

    provider_impl = PROVIDERS.get(provider_name)
    if provider_impl is None:
        raise ValueError(f"Provider '{provider_name}' is not configured")

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
        "route_source": selected.route_source,
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

    computed_cost, baseline_cost = compute_costs(
        provider=provider_name,
        model=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    cost_usd = computed_cost if computed_cost > 0 else float(result.get("cost_usd", 0.0))
    if baseline_cost <= 0:
        baseline_cost = cost_usd if cost_usd > 0 else float(result.get("cost_usd", 0.0))

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

    alri_score, alri_tier = compute_alri_v2(
        band=selected.band,
        provider=provider_name,
        model=model_name,
        prompt_tokens=int(prompt_tokens or 0),
        completion_tokens=int(completion_tokens or 0),
        cost_usd=result["cost_usd"],
        baseline_cost_usd=baseline_cost,
        overrides_used=overrides_used,
    )

    t_done = time.perf_counter()
    total_latency_ms = (t_done - t_start) * 1000.0
    router_latency_ms = (t_router_done - t_start) * 1000.0
    provider_latency_ms = (t_provider_end - t_provider_start) * 1000.0
    processing_latency_ms = max(
        0.0, total_latency_ms - router_latency_ms - provider_latency_ms
    )

    log_run(
        db,

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
    )

    # ---- Response ----
    provenance = result.get("provenance") or {}
    provenance.update(
        {
            "provider": provider_name,
            "model": model_name,
            "route_source": selected.route_source,
        }
    )
    result["provenance"] = provenance

    resp = RunResponse(
        run_id=rid,
        status="ok" if not pol["hil_triggered"] else "hil_required",
        output=result["output"],
        confidence=result["confidence"],
        provenance=Provenance(**result["provenance"]),
        policy_evaluation=PolicyEvaluation(**pol),
        metrics=MetricsInfo(latency_ms=int(total_latency_ms), cost_usd=result["cost_usd"]),
        audit=AuditInfo(retention_class=alri_tag, audit_hash=None)
    )

    log_event("router_out", {"run_id": rid, "status": resp.status})
    return JSONResponse(resp.model_dump())
