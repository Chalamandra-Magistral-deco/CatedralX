"""Normalize observed sensor and market payloads to the PERCEIVE canonical format."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from .snapshot_signing import gap_inertia_in_range


def validate_price_history(values: Any, minimum: int = 30) -> list[float]:
    """Return observed prices as finite positive floats; never synthesize history."""
    if not isinstance(values, (list, tuple)):
        raise ValueError("price history must be a list or tuple of observed prices")
    if len(values) < minimum:
        raise ValueError(f"at least {minimum} observed prices are required")

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


def _first_present(payload: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in payload:
            return payload[name]
    return None


def _validate_observed_at(value: Any) -> str:
    """Require the source observation timestamp; never replace it with wall time."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("observed_at must be supplied by the observation source")
    observed_at = value.strip()
    try:
        parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("observed_at must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("observed_at must include a timezone")
    return observed_at


def _finite_return(payload: dict[str, Any], field: str) -> float:
    value = payload.get(field, 0.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a numeric 1-minute return")
    number = float(value)
    if not gap_inertia_in_range(number):
        raise ValueError(f"{field} must be finite and in [-1, 1]")
    return number


def normalize_market_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize supported provider aliases without inventing observations."""
    if not isinstance(payload, dict):
        raise ValueError("market payload must be an object")

    raw_history = _first_present(
        payload, ("historial_precios", "historico", "precios", "history", "ohlc", "valores")
    )
    if raw_history is None:
        raise ValueError("observed price history is required")
    if isinstance(raw_history, list) and any(isinstance(item, dict) for item in raw_history):
        extracted: list[Any] = []
        for index, item in enumerate(raw_history):
            if not isinstance(item, dict):
                extracted.append(item)
                continue
            value = _first_present(item, ("precio", "valor", "close", "price"))
            if value is None:
                raise ValueError(f"history item {index} has no recognized price field")
            extracted.append(value)
        raw_history = extracted
    prices = validate_price_history(raw_history)

    raw_current = _first_present(
        payload, ("precio_actual", "precio", "last_price", "close", "valor")
    )
    if raw_current is None:
        current = prices[-1]
    else:
        if isinstance(raw_current, bool):
            raise ValueError("precio must be positive and finite")
        try:
            current = float(raw_current)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("precio must be positive and finite") from exc
        if not math.isfinite(current) or current <= 0:
            raise ValueError("precio must be positive and finite")

    if prices[-1] != current:
        prices.append(current)

    observed_at = _validate_observed_at(
        _first_present(payload, ("observed_at", "timestamp", "tiempo", "fecha", "datetime"))
    )
    raw_source = _first_present(payload, ("source", "fuente", "exchange", "origen", "provider"))
    if raw_source is None:
        source = "unspecified"
    elif isinstance(raw_source, str) and raw_source.strip():
        source = raw_source.strip()
    else:
        raise ValueError("source must be a non-empty string when provided")

    gap = _finite_return(payload, "gap")
    inertia = _finite_return(payload, "inercia")

    return {
        "historial_precios": prices,
        "precio": current,
        "gap": gap,
        "inercia": inertia,
        "source": source,
        "observed_at": observed_at,
    }
