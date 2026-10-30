"""Unit tests for the analysis-only public-candle historical evaluator."""
from __future__ import annotations

import math

from scripts.backtest_public_candles import evaluate, future_label


def synthetic_candles(count: int, drift: float = 0.0008):

    start = 1_800_000_000_000
    rows = []
    for index in range(count):
        price = 100.0 * math.exp(drift * index + 0.0001 * math.sin(index))
        opened = start + index * 60_000
        rows.append({
            "open_time_ms": opened,
            "close_time_ms": opened + 59_999,
            "close": price,
            "open": price,
            "high": price * 1.0001,
            "low": price * 0.9999,
            "volume": 10.0,
        })
    return rows


def test_future_label_uses_explicit_percent_threshold():
    assert future_label(0.05, 0.05) == "buy"
    assert future_label(-0.05, 0.05) == "sell"
    assert future_label(0.049, 0.05) == "hold"


def test_evaluate_uses_forward_horizon_and_never_enables_orders():
    candles = synthetic_candles(140)
    result = evaluate(candles, horizon=5, threshold_pct=0.05)
    assert result["evaluation"]["predictions_evaluated"] == 140 - 60 - 5 + 1
    assert result["market_data"]["closed_candles"] == 140
    assert result["all_period"]["samples"] == result["evaluation"]["predictions_evaluated"]
    assert result["safety"]["analysis_only"] is True
    assert result["safety"]["trading_enabled"] is False
    assert result["safety"]["orders_created"] is False
    assert result["safety"]["orders_executed"] is False
    assert result["all_period"]["always_hold_accuracy_baseline"] is not None


def test_evaluate_chronological_halves_cover_all_samples():
    result = evaluate(synthetic_candles(200), horizon=5)
    first = result["first_chronological_half"]["samples"]
    second = result["second_chronological_half"]["samples"]
    assert first + second == result["all_period"]["samples"]
    assert result["first_chronological_half"]["from_utc"] < result["second_chronological_half"]["from_utc"]
