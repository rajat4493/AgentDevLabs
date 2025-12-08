"""
Basic regex/keyword-based PII + PHI tagging helpers.
"""

from __future__ import annotations

import re
from typing import List, Set

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")

PHI_KEYWORDS = {"doctor", "diagnosis", "prescription", "hospital", "patient", "medical"}
FINANCIAL_KEYWORDS = {"salary", "bank", "loan", "credit", "mortgage", "account number"}


def _scan_keywords(text: str, keywords: Set[str]) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in keywords)


def detect_tags(text: str | None) -> List[str]:
    """
    Return lightweight tags describing sensitive content without storing the text.
    """

    if not text:
        return []

    tags: Set[str] = set()
    if EMAIL_RE.search(text):
        tags.add("PII_EMAIL")
    if PHONE_RE.search(text):
        tags.add("PII_PHONE")
    if CREDIT_CARD_RE.search(text):
        tags.add("PII_FINANCIAL_CARD")
    if _scan_keywords(text, PHI_KEYWORDS):
        tags.add("PHI_MEDICAL")
    if _scan_keywords(text, FINANCIAL_KEYWORDS):
        tags.add("FINANCIAL_TERMS")
    return sorted(tags)


__all__ = ["detect_tags"]
