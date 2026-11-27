"""Flag unusually large single-step observed price changes."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any


def detectar_movimiento(precios: Sequence[float], threshold: float = 0.002) -> dict[str, Any]:
    if isinstance(threshold, bool):
        raise ValueError("threshold must be positive and finite")
    try:
        threshold_value = float(threshold)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("threshold must be positive and finite") from exc
    if not math.isfinite(threshold_value) or threshold_value <= 0:
        raise ValueError("threshold must be positive and finite")
    if isinstance(precios, (str, bytes)) or not isinstance(precios, Sequence):
        raise ValueError("prices must be a numeric sequence")
    if len(precios) < 2:
        return {"detected": False, "change_fraction": 0.0, "threshold": threshold_value}
    converted = []
    for value in precios[-2:]:
        if isinstance(value, bool):
            raise ValueError("prices must be positive and finite")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("prices must be positive and finite") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError("prices must be positive and finite")
        converted.append(number)
    previous, current = converted
    change = current / previous - 1.0
    return {"detected": abs(change) > threshold_value,
            "change_fraction": change, "threshold": threshold_value}
