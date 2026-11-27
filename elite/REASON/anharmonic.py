"""Projective cross-ratio features for a price series.

The public API intentionally remains analyze(precios) -> (cross_ratio, score).
Degenerate projective configurations return the legacy neutral pair (0.0, 0.0);
malformed or non-finite market data is rejected instead of being propagated.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Sequence


def analyze(precios: Sequence[Real]) -> tuple[float, float]:
    """Return the cross-ratio and a bounded relative-dispersion score.

    Only the last four observations participate in the calculation. Fewer
    than four observations preserve the historical neutral result. The
    selected observations must be real, finite, strictly positive prices.

    (0.0, 0.0) is returned for a degenerate cross-ratio denominator.
    Invalid input or a non-finite computed result raises ValueError.
    """
    if not isinstance(precios, (list, tuple)):
        raise TypeError("precios debe ser una lista o tupla de números")

    if len(precios) < 4:
        return 0.0, 0.0

    values: list[float] = []
    for value in precios[-4:]:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("los precios deben ser valores numéricos reales")
        number = float(value)
        if not math.isfinite(number) or number <= 0.0:
            raise ValueError("los precios deben ser finitos y estrictamente positivos")
        values.append(number)

    k1, k2, k3, support = values
    left_denominator = k2 - support
    right_denominator = k1 - k3
    if left_denominator == 0.0 or right_denominator == 0.0:
        return 0.0, 0.0

    # Factor the quotient to avoid overflowing the product of differences.
    cross_ratio = ((k1 - support) / right_denominator) * (
        (k2 - k3) / left_denominator
    )
    if not math.isfinite(cross_ratio):
        raise ValueError("el cross-ratio calculado no es finito")

    # Scale before summing so a valid large price level cannot overflow.
    scale = max(values)
    scaled_mean = math.fsum(value / scale for value in values) / len(values)
    baseline = scaled_mean * scale
    spread = max(values) - min(values)
    score = min(1.0, spread / baseline)

    if not math.isfinite(score):
        raise ValueError("el indicador de dispersión calculado no es finito")
    return float(cross_ratio), float(score)
