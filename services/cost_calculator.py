"""
Estimated API cost calculation, based on config/pricing.py rates.
"""
from config.pricing import get_rate


def calculate_cost(provider: str, tier: str, input_tokens: int, output_tokens: int) -> float:
    rate = get_rate(provider, tier)
    input_cost = (input_tokens / 1_000_000) * rate["input_cost_per_million_tokens"]
    output_cost = (output_tokens / 1_000_000) * rate["output_cost_per_million_tokens"]
    total_cost = input_cost + output_cost
    return round(total_cost, 6)
