from enum import Enum
from typing import Tuple


class QueryCategory(str, Enum):
    CODING = "coding"
    DATA = "data"
    PRODUCT = "product"
    OPERATIONS = "operations"
    LEGAL = "legal"
    COMPLIANCE = "compliance"
    FINANCE = "finance"
    GENERAL = "general"
    CREATIVE = "creative"
    UNKNOWN = "unknown"


def classify_query(text: str) -> Tuple[QueryCategory, float]:
    """
    Very fast, rule-based V1.
    Returns (category, confidence). Confidence is a rough heuristic (0-1).

    NOTE: This will evolve. Treat it as a heuristic, not ground truth.
    """
    t = text.lower()

    # --- CODING ---
    generic_coding_patterns = [
    "how to write code",
    "how to write a code",
    "how to write code in",
    "how to write a code in",
    "how to code in",
    "write code in",
    "write a code in",
    "generate code",
    "create code",
    "example code",
    ]
    if any(p in t for p in generic_coding_patterns):
        return QueryCategory.CODING, 0.95
    
    languages = [
    "python", "typescript", "javascript", "java", "c#", "c++",
    "golang", "go ", "rust", "php", "kotlin", "swift"
    ]

    if any(lang in t for lang in languages):
        return QueryCategory.CODING, 0.9
    
    coding_keywords = [
        "python",
        "java",
        "c#",
        "c++",
        "javascript",
        "typescript",
        "go ",
        "golang",
        "rust",
        "php",
        "kotlin",
        "swift",
        "react",
        "node.js",
        "nodejs",
        "spring boot",
        "django",
        "flask",
        "fastapi",
        "bug",
        "stack trace",
        "segmentation fault",
        "nullpointer",
        "null pointer",
        "exception",
        "error:",
        "traceback",
        "unit test",
        "test case",
        "refactor",
        "algorithm",
        "time complexity",
        "space complexity",
        "class ",
        "def ",
        "function(",
        "lambda ",
        "bash script",
        "shell script",
        "powershell",
    ]

    if any(k in t for k in coding_keywords):
        return QueryCategory.CODING, 0.9

    # --- DATA / SQL / BI ---
    data_keywords = [
        "sql",
        "select * from",
        "inner join",
        "left join",
        "group by",
        "order by",
        "dataframe",
        "pandas",
        "power bi",
        "dax ",
        "measure ",
        "tableau",
        "bigquery",
        "snowflake",
        "data warehouse",
        "etl",
        "elt",
    ]
    if any(k in t for k in data_keywords):
        return QueryCategory.DATA, 0.85

    # --- LEGAL ---
    legal_keywords = [
        "clause",
        "contract",
        "agreement",
        "liability",
        "indemnity",
        "governing law",
        "jurisdiction",
        "term and termination",
        "non-compete",
        "non compete",
        "nda",
        "non-disclosure",
        "non disclosure",
        "ip ownership",
        "intellectual property",
    ]
    if any(k in t for k in legal_keywords):
        return QueryCategory.LEGAL, 0.8

    # --- COMPLIANCE / RISK ---
    compliance_keywords = [
        "kyc",
        "k y c",
        "aml",
        "a m l",
        "pep",
        "sanctions",
        "customer due diligence",
        "transaction monitoring",
        "source of funds",
        "source of wealth",
        "risk assessment",
        "risk score",
        "suspicious activity",
        "suspicious transaction",
    ]
    if any(k in t for k in compliance_keywords):
        return QueryCategory.COMPLIANCE, 0.85

    # --- FINANCE ---
    finance_keywords = [
        "revenue",
        "ebitda",
        "p&l",
        "pnl",
        "profit and loss",
        "cash flow",
        "cashflow",
        "forecast",
        "budget",
        "valuation",
        "discounted cash flow",
        "npv",
        "irr",
        "balance sheet",
        "income statement",
    ]
    if any(k in t for k in finance_keywords):
        return QueryCategory.FINANCE, 0.8

    # --- PRODUCT / UX ---
    product_keywords = [
        "roadmap",
        "product requirement",
        "feature request",
        "user story",
        "acceptance criteria",
        "mvp",
        "minimum viable product",
        "backlog",
        "release plan",
        "sprint goal",
        "user journey",
        "wireframe",
    ]
    if any(k in t for k in product_keywords):
        return QueryCategory.PRODUCT, 0.75

    # --- OPERATIONS / SUPPORT ---
    ops_keywords = [
        "sla",
        "aht",
        "average handling time",
        "ticket",
        "queue",
        "incident",
        "service request",
        "zendesk",
        "jira",
        "throughput",
        "escalation",
        "kb article",
        "knowledge base",
    ]
    if any(k in t for k in ops_keywords):
        return QueryCategory.OPERATIONS, 0.8

    # --- CREATIVE / WRITING ---
    # NOTE: removed "script" to avoid conflict with coding prompts.
    creative_keywords = [
        "story",
        "short story",
        "poem",
        "lyrics",
        "song",
        "blog post",
        "hook",
        "novel",
        "character",
        "worldbuilding",
    ]
    if any(k in t for k in creative_keywords):
        return QueryCategory.CREATIVE, 0.8

    # Default fallback
    return QueryCategory.GENERAL, 0.5
