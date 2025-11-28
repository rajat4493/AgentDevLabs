from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RunRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or task")
    agent_id: Optional[str] = Field(default="default-agent")
    context: Optional[Dict[str, Any]] = None
    policy_overrides: Optional[Dict[str, Any]] = None
    router_mode: Optional[str] = Field(
        default=None, description="Optional router mode override (baseline/enhanced)"
    )
    band: Optional[str] = Field(default=None, description="Optional requested band (low/medium/high)")
    task_type: Optional[str] = Field(default=None, description="Optional task type hint (default/code)")
    force_provider: Optional[str] = None
    force_model: Optional[str] = None
    force_band: Optional[str] = None

class Provenance(BaseModel):
    provider: str
    model: str
    route_source: Optional[str] = None
    parameters: Dict[str, Any] = {}

class PolicyEvaluation(BaseModel):
    allow_list_passed: bool = True
    confidence_threshold: float = 0.7
    hil_triggered: bool = False
    violations: list[str] = []

class AuditInfo(BaseModel):
    retention_class: str
    audit_hash: Optional[str] = None  # placeholder for future hash-chain

class MetricsInfo(BaseModel):
    latency_ms: int
    cache: str = "miss"
    cost_usd: float

class RunResponse(BaseModel):
    run_id: str
    status: str
    output: str
    confidence: float
    provenance: Provenance
    policy_evaluation: PolicyEvaluation
    metrics: MetricsInfo
    audit: AuditInfo

class MetricsSnapshot(BaseModel):
    total_runs: int
    avg_latency_ms: float
    total_cost_usd: float
