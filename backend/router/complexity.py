import re

RISK_KEYWORDS = [
    "analyze",
    "optimize",
    "summarize",
    "compare",
    "design",
    "explain",
    "policy",
    "architecture",
    "draft",
    "contract",
    "clause",
    "compliance",
    "legal",
    "governance",
    "security",
    "regulation",
    "migration",
]

def score_complexity(prompt: str) -> float:
    """
    Lightweight heuristic complexity score in [0,1].
    Factors: length, numerics, code fences/JSON, sentences, keywords.
    """
    if not prompt:
        return 0.0

    # length factor
    n_chars = len(prompt)
    f_len = min(n_chars / 2000.0, 1.0)

    # numerics & symbols
    f_digits = min(len(re.findall(r"\d", prompt)) / 50.0, 1.0)
    f_symbols = min(len(re.findall(r"[\{\}\[\]\(\)\=\+\-\*/<>]", prompt)) / 80.0, 1.0)

    # code/JSON fences
    f_code = 0.2 if "```" in prompt or re.search(r"\bclass\b|\bdef\b|\bfunction\b", prompt) else 0.0
    f_json = 0.2 if re.search(r"\{.*:.*\}", prompt, flags=re.S) else 0.0

    # sentences (rough)
    f_sent = min(len(re.split(r"[.!?]+", prompt)) / 20.0, 1.0)

    # keywords hinting complexity
    keywords = [k for k in RISK_KEYWORDS if k in prompt.lower()]
    f_kw = min(0.1 * len(keywords), 0.3)

    score = (
        (0.45 * f_len)
        + (0.15 * f_digits)
        + (0.1 * f_symbols)
        + f_code
        + f_json
        + (0.2 * f_sent)
        + f_kw
    )
    return max(0.0, min(score, 1.0))

LONG_CONTEXT_CHAR_THRESHOLD = 4000


def choose_band(score: float, prompt: str | None = None) -> str:
    text = prompt or ""
    text_len = len(text)
    lower_text = text.lower()
    keyword_hits = sum(1 for k in RISK_KEYWORDS if k in lower_text)

    if text_len >= LONG_CONTEXT_CHAR_THRESHOLD:
        return "long_context"
    if text_len >= 900 or score >= 0.65 or keyword_hits >= 3:
        return "complex"
    if text_len <= 160 and score <= 0.12 and keyword_hits == 0:
        return "simple"
    if score < 0.35 and text_len < 350 and keyword_hits <= 1:
        return "simple"
    return "moderate"
