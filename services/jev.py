"""
Jev Decision Layer.

Jev is NOT a token-monitoring platform. It is a decision layer that analyses
an incoming task/prompt and decides:
  - Task complexity (LOW / MEDIUM / HIGH / CRITICAL)
  - Recommended model tier / route (CHEAP / STANDARD / ADVANCED / ADVANCED+HUMAN REVIEW)
  - Whether human review is required

If TYPESAFE_API_KEY is configured, this module would call the real Jev/Typesafe
API. For this POC there is no live Jev API to call against, so "real" mode is
a placeholder integration point. If it fails for any reason, we automatically
fall back to demo (local heuristic) mode and log the error.
"""
import logging

from config.settings import TYPESAFE_API_KEY, is_jev_configured

logger = logging.getLogger("jev")

COMPLEXITY_ROUTES = {
    "LOW": {"tier": "cheap", "route": "CHEAP", "human_review": False},
    "MEDIUM": {"tier": "standard", "route": "STANDARD", "human_review": False},
    "HIGH": {"tier": "advanced", "route": "ADVANCED", "human_review": False},
    "CRITICAL": {"tier": "advanced", "route": "ADVANCED + HUMAN REVIEW", "human_review": True},
}

CRITICAL_KEYWORDS = [
    "security", "vulnerability", "exploit", "production migration", "prod migration",
    "compliance", "gdpr", "credentials", "payment", "pii", "breach", "penetration test",
]

HIGH_KEYWORDS = [
    "architecture", "debug", "debugging", "refactor", "large analysis", "root cause",
    "performance", "scalability", "system design", "migration", "optimi", "distributed",
]

MEDIUM_KEYWORDS = [
    "write code", "function", "script", "content", "blog", "summarize", "email",
    "documentation", "test case", "feature", "bug fix",
]


def _demo_decision(prompt: str) -> dict:
    """Local heuristic fallback used when no real Jev API is configured."""
    text = (prompt or "").strip().lower()
    word_count = len(text.split())

    if any(kw in text for kw in CRITICAL_KEYWORDS):
        complexity = "CRITICAL"
    elif any(kw in text for kw in HIGH_KEYWORDS) or word_count > 80:
        complexity = "HIGH"
    elif any(kw in text for kw in MEDIUM_KEYWORDS) or word_count > 15:
        complexity = "MEDIUM"
    elif word_count == 0:
        complexity = "LOW"
    else:
        complexity = "LOW"

    route_info = COMPLEXITY_ROUTES[complexity]
    return {
        "complexity": complexity,
        "tier": route_info["tier"],
        "route": route_info["route"],
        "human_review": route_info["human_review"],
        "confidence": 0.72,
        "decision_source": "demo",
    }


def _real_jev_decision(prompt: str) -> dict:
    """
    Placeholder for the real Jev/Typesafe API integration.

    This POC has no live Jev endpoint to call. When one is available, implement
    the HTTP call here using TYPESAFE_API_KEY, parse its response into the same
    shape as `_demo_decision`, and return it. Any exception must propagate so
    the caller falls back to demo mode.
    """
    raise NotImplementedError("Real Jev API integration is not yet available")


def get_jev_decision(prompt: str) -> dict:
    """
    Main entry point used by the app. Returns a dict:
    {complexity, tier, route, human_review, confidence, decision_source}
    Falls back to demo mode automatically on any failure.
    """
    if is_jev_configured():
        try:
            return _real_jev_decision(prompt)
        except Exception as exc:
            logger.warning("Jev real API failed, falling back to demo mode: %s", exc)
            return _demo_decision(prompt)
    return _demo_decision(prompt)
