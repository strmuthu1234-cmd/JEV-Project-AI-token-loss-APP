"""
Model routing: maps a Jev-recommended tier + chosen provider to the
configured model name for that provider/tier.
"""
from config.settings import (
    OPENAI_CHEAP_MODEL, OPENAI_STANDARD_MODEL, OPENAI_ADVANCED_MODEL,
    ANTHROPIC_CHEAP_MODEL, ANTHROPIC_STANDARD_MODEL, ANTHROPIC_ADVANCED_MODEL,
)

MODEL_MAP = {
    "openai": {
        "cheap": OPENAI_CHEAP_MODEL,
        "standard": OPENAI_STANDARD_MODEL,
        "advanced": OPENAI_ADVANCED_MODEL,
    },
    "anthropic": {
        "cheap": ANTHROPIC_CHEAP_MODEL,
        "standard": ANTHROPIC_STANDARD_MODEL,
        "advanced": ANTHROPIC_ADVANCED_MODEL,
    },
}


def resolve_model(provider: str, tier: str) -> str:
    provider = provider.lower()
    tier = tier.lower()
    if provider not in MODEL_MAP or tier not in MODEL_MAP[provider]:
        raise ValueError(f"Unknown provider/tier combination: {provider}/{tier}")
    return MODEL_MAP[provider][tier]
