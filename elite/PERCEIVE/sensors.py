"""Validate observed market observations; never invent missing prices."""
from __future__ import annotations

import math
from typing import Any

from .snapshot_signing import gap_inertia_in_range


def validate_price_history(values: Any, minimum: int = 30) -> list[float]:
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise ValueError("minimum must be a positive integer")
    if not isinstance(values, (list, tuple)):
        raise ValueError("price history must be a list or tuple of observed prices")
    if len(values) < minimum:
        raise ValueError(f"at least {minimum} observed prices are required; received {len(values)}")
    result: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool):
            raise ValueError(f"price[{index}] must be positive and finite")
        try:
            price = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"price[{index}] must be positive and finite") from exc
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"price[{index}] must be positive and finite")
        result.append(price)
    return result


def normalize_market_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("market payload must be an object")
    raw_history = payload.get("historial_precios", payload.get("historico"))
    if raw_history is None:
        raise ValueError("missing price history (historial_precios or historico)")
    prices = validate_price_history(raw_history)
    current_raw = payload.get("precio")
    if current_raw is None:
        current = prices[-1]
    else:
        if isinstance(current_raw, bool):
            raise ValueError("precio must be positive and finite")
        try:
            current = float(current_raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("precio must be positive and finite") from exc
        if not math.isfinite(current) or current <= 0:
            raise ValueError("precio must be positive and finite")
        if not math.isclose(prices[-1], current, rel_tol=1e-12, abs_tol=0.0):
            prices.append(current)

    features: dict[str, float] = {}
    for field in ("gap", "inercia"):
        raw = payload.get(field, 0.0)
        if isinstance(raw, bool):
            raise ValueError(f"{field} must be a numeric 1-minute return")
        try:
            value = float(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field} must be a numeric 1-minute return") from exc
        if not math.isfinite(value) or not gap_inertia_in_range(value):
            raise ValueError(f"{field} must be finite and in [-1, 1]")
        features[field] = value

    source = payload.get("source", "unspecified")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    observed_at = payload.get("observed_at")
    if observed_at is not None and (not isinstance(observed_at, str) or not observed_at.strip()):
        raise ValueError("observed_at must be a non-empty ISO-8601 string when provided")

    return {
        "historial_precios": prices,
        "precio": current,
        "gap": features["gap"],
        "inercia": features["inercia"],
        "source": source,
        "observed_at": observed_at,
    }
