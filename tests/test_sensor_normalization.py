"""Fail-closed tests for PERCEIVE market payload normalization."""

import math

import pytest

from PERCEIVE.sensors import normalize_market_payload, validate_price_history


def valid_payload():
    prices = [100.0 + index for index in range(30)]
    return {
        "precio_actual": prices[-1],
        "historial_precios": prices,
        "observed_at": "2026-11-18T23:40:00-06:00",
        "source": "synthetic-smoke-test",
    }


def test_normalizes_provider_aliases_without_changing_observation_time():
    prices = [100.0 + index for index in range(30)]
    payload = {
        "last_price": prices[-1],
        "history": prices,
        "timestamp": "2026-11-18T23:40:00Z",
        "provider": "synthetic-smoke-test",
        "gap": 0.01,
        "inercia": -0.02,
    }

    result = normalize_market_payload(payload)

    assert result["precio"] == prices[-1]
    assert result["historial_precios"] == prices
    assert result["observed_at"] == payload["timestamp"]
    assert result["source"] == payload["provider"]
    assert result["gap"] == 0.01
    assert result["inercia"] == -0.02


def test_rejects_missing_observation_timestamp_instead_of_fabricating_one():
    payload = valid_payload()
    payload.pop("observed_at")

    with pytest.raises(ValueError, match="observed_at must be supplied"):
        normalize_market_payload(payload)


@pytest.mark.parametrize("bad_price", [True, float("nan"), float("inf"), 0, -1])
def test_rejects_invalid_prices(bad_price):
    payload = valid_payload()
    payload["historial_precios"][-1] = bad_price

    with pytest.raises(ValueError, match="positive and finite"):
        normalize_market_payload(payload)


@pytest.mark.parametrize("field", ["gap", "inercia"])
@pytest.mark.parametrize("bad_value", [True, float("nan"), float("inf"), 1.01, -1.01, "0.1"])
def test_rejects_invalid_return_features(field, bad_value):
    payload = valid_payload()
    payload[field] = bad_value

    with pytest.raises(ValueError, match=field):
        normalize_market_payload(payload)


def test_rejects_invalid_timezone_and_source_types():
    payload = valid_payload()
    payload["observed_at"] = "2026-11-18T23:40:00"

    with pytest.raises(ValueError, match="timezone"):
        normalize_market_payload(payload)

    payload = valid_payload()
    payload["source"] = {"provider": "unknown"}
    with pytest.raises(ValueError, match="source must be a non-empty string"):
        normalize_market_payload(payload)


def test_history_validator_rejects_boolean_and_non_finite_values():
    with pytest.raises(ValueError):
        validate_price_history([100.0] * 29 + [True])
    with pytest.raises(ValueError):
        validate_price_history([100.0] * 29 + [math.nan])
