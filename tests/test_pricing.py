import pytest

from underwriter.pricing import (
    GPT_4O_INPUT_USD_PER_TOKEN,
    GPT_4O_OUTPUT_USD_PER_TOKEN,
    compute_cost,
)


def test_pricing_constants_match_spec():
    assert GPT_4O_INPUT_USD_PER_TOKEN == pytest.approx(2.50 / 1_000_000)
    assert GPT_4O_OUTPUT_USD_PER_TOKEN == pytest.approx(10.00 / 1_000_000)


def test_compute_cost_zero_usage():
    assert compute_cost({"input_tokens": 0, "output_tokens": 0}) == 0.0


def test_compute_cost_typical_run():
    expected = 1000 * (2.50 / 1_000_000) + 500 * (10.00 / 1_000_000)
    assert compute_cost({"input_tokens": 1000, "output_tokens": 500}) == pytest.approx(expected)


def test_compute_cost_missing_keys_defaults_zero():
    assert compute_cost({}) == 0.0
    assert compute_cost({"input_tokens": 100}) == pytest.approx(100 * 2.50 / 1_000_000)
    assert compute_cost({"output_tokens": 100}) == pytest.approx(100 * 10.00 / 1_000_000)
