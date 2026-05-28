"""OpenAI gpt-4o pricing constants + per-usage USD cost calculator.

Update GPT_4O_*_USD_PER_TOKEN when OpenAI changes pricing. Values as of 2026-05.
"""

GPT_4O_INPUT_USD_PER_TOKEN = 2.50 / 1_000_000
GPT_4O_OUTPUT_USD_PER_TOKEN = 10.00 / 1_000_000


def compute_cost(usage: dict) -> float:
    """Compute USD cost from a usage dict {'input_tokens': int, 'output_tokens': int}."""
    return (
        usage.get("input_tokens", 0) * GPT_4O_INPUT_USD_PER_TOKEN
        + usage.get("output_tokens", 0) * GPT_4O_OUTPUT_USD_PER_TOKEN
    )
