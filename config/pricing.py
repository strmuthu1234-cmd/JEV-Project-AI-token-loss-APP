"""
Configurable pricing table for AI providers/models.
All rates are USD per 1,000,000 tokens. Update as provider pricing changes.
"""

PRICING = {
    "openai": {
        "cheap": {
            "input_cost_per_million_tokens": 0.15,
            "output_cost_per_million_tokens": 0.60,
        },
        "standard": {
            "input_cost_per_million_tokens": 2.50,
            "output_cost_per_million_tokens": 10.00,
        },
        "advanced": {
            "input_cost_per_million_tokens": 5.00,
            "output_cost_per_million_tokens": 15.00,
        },
    },
    "anthropic": {
        "cheap": {
            "input_cost_per_million_tokens": 0.25,
            "output_cost_per_million_tokens": 1.25,
        },
        "standard": {
            "input_cost_per_million_tokens": 3.00,
            "output_cost_per_million_tokens": 15.00,
        },
        "advanced": {
            "input_cost_per_million_tokens": 15.00,
            "output_cost_per_million_tokens": 75.00,
        },
    },
}


def get_rate(provider: str, tier: str) -> dict:
    """Return the input/output per-million-token rate for a provider/tier."""
    provider = provider.lower()
    tier = tier.lower()
    if provider not in PRICING or tier not in PRICING[provider]:
        # Fallback to standard OpenAI pricing if an unknown combination is requested
        return PRICING["openai"]["standard"]
    return PRICING[provider][tier]
