from __future__ import annotations

import re
from typing import Optional, Tuple


PII_PATTERNS = [
    r"\biban\b",
    r"\bic\s*code\b",
    r"\baccount\s*id\b",
    r"\bssn\b",
    r"\bpassport\b",
    r"\bclient\s*id\b",
]
CARD_PATTERN = r"\b\d{4}[- ]?\d{4}[- ]?\d{4}"
REGULATORY_KEYWORDS = [
    "gdpr",
    "hipaa",
    "psd2",
    "aml",
    "kyd",
    "kya",
    "audit",
    "regulatory",
    "compliance",
]
FRAUD_KEYWORDS = [
    "dispute",
    "chargeback",
    "fraud",
    "suspicious",
    "unauthorized transaction",
    "unauthorized",
]


def compute_alri_v2(
    *,
    band: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    baseline_cost_usd: float,
    overrides_used: bool = False,
    governance_level: Optional[int] = None,
    business_impact_level: Optional[int] = None,
    safety_flag_level: Optional[int] = None,
    prompt_text: Optional[str] = None,
) -> Tuple[float, str]:
    """
    Heuristic ALRI score and tier.
    """
    band_lower = (band or "").lower()
    base_map = {
        "simple": 2.0,
        "low": 2.0,
        "moderate": 4.0,
        "medium": 4.0,
        "complex": 6.5,
        "high": 6.5,
        "long_context": 6.5,
    }
    score = base_map.get(band_lower, 4.0)

    text = (prompt_text or "").lower()
    pii_hits = 0
    for pattern in PII_PATTERNS:
        if re.search(pattern, text):
            pii_hits += 1
    if re.search(CARD_PATTERN, text):
        pii_hits += 1
    if "customer" in text and ("id" in text or "account" in text):
        pii_hits += 1

    if any(keyword in text for keyword in REGULATORY_KEYWORDS):
        score += 2.0

    if any(keyword in text for keyword in FRAUD_KEYWORDS):
        score += 1.5

    score += pii_hits * 1.5

    if cost_usd and cost_usd > 0.01:
        score += 0.5

    if overrides_used:
        score += 0.5

    if safety_flag_level:
        score += min(1.0, safety_flag_level * 0.5)

    if governance_level:
        score += min(1.0, governance_level * 0.5)

    if business_impact_level:
        score += min(1.0, business_impact_level * 0.5)

    score = max(0.0, min(score, 10.0))

    if score >= 8.0:
        tier = "red_critical"
    elif score >= 6.0:
        tier = "orange_high"
    elif score >= 3.5:
        tier = "yellow_medium"
    else:
        tier = "green_low"

    return round(score, 1), tier
