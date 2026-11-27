"""Bounded market-surprise diagnostic with explicit feedback-state validation.

This is a heuristic surprise score, not a Bayesian variational free-energy
estimator and not a calibrated probability.
"""
from __future__ import annotations

import math


MAX_FREE_ENERGY = 20.0


def _finite_number(name: str, value: object) -> float:
    """Return a finite float, rejecting bools and implicit coercions."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} debe ser un número finito.")
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} debe ser un número finito.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} debe ser un número finito.")
    return number


def coherencia_desde_energia_previa(energia_previa: float) -> float:
    """Map a valid previous surprise score in [0, 20] to heuristic coherence.

    The mapping is deliberately bounded: zero prior surprise maps to 1;
    maximum prior surprise maps to 0. It is a feedback state, not a
    statistical coherence estimate.
    """
    previous = _finite_number("energia_previa", energia_previa)
    if not 0.0 <= previous <= MAX_FREE_ENERGY:
        raise ValueError("energia_previa debe estar dentro de [0, 20].")
    return max(0.0, min(1.0, 1.0 - previous / MAX_FREE_ENERGY))


def free_energy(
    prediccion_tendencia: float,
    realidad_gap: float,
    inercia_observada: float,
    retorno_actual: float = 0.0,
    coherencia_previa: float = 0.5,
) -> float:
    """Calculate bounded heuristic surprise from prediction and observations.

    Inputs:
      - prediccion_tendencia: normalized trend estimate in [0, 1].
      - realidad_gap: absolute, normalized gap magnitude in [0, 1].
      - inercia_observada: normalized observed inertia in [-1, 1].
      - retorno_actual: finite observed log return.
      - coherencia_previa: bounded feedback state in [0, 1].

    The output is always in [0, 20]. Invalid inputs raise ValueError rather
    than being converted into a misleading zero-surprise observation.
    """
    prediction = _finite_number("prediccion_tendencia", prediccion_tendencia)
    gap = _finite_number("realidad_gap", realidad_gap)
    inertia = _finite_number("inercia_observada", inercia_observada)
    current_return = _finite_number("retorno_actual", retorno_actual)
    coherence = _finite_number("coherencia_previa", coherencia_previa)

    if not 0.0 <= prediction <= 1.0:
        raise ValueError("prediccion_tendencia debe estar dentro de [0, 1].")
    if not 0.0 <= gap <= 1.0:
        raise ValueError("realidad_gap debe ser magnitud normalizada dentro de [0, 1].")
    if not -1.0 <= inertia <= 1.0:
        raise ValueError("inercia_observada debe estar dentro de [-1, 1].")
    if not 0.0 <= coherence <= 1.0:
        raise ValueError("coherencia_previa debe estar dentro de [0, 1].")

    # Keep the existing score semantics while making each term explicit.
    return_component = abs(current_return) * 10.0
    gap_component = min(1.0, gap * 200.0)

    expected_inertia = 2.0 * (prediction - 0.5)
    inertia_component = min(1.0, abs(inertia - expected_inertia) / 2.0)

    incoherence_multiplier = 2.0 - coherence
    raw_score = (
        return_component + gap_component + inertia_component
    ) * incoherence_multiplier * 2.5

    # All terms are non-negative; this cap also safely handles finite inputs
    # whose intermediate multiplication exceeds the float range.
    return float(min(MAX_FREE_ENERGY, max(0.0, raw_score)))


def prediccion_interna(hurst: float, cross_ratio: float) -> float:
    """Estimate a bounded trend-strength diagnostic from Hurst and cross-ratio.

    This is a heuristic score, not a calibrated continuation probability.
    """
    hurst_value = _finite_number("hurst", hurst)
    ratio_value = _finite_number("cross_ratio", cross_ratio)
    if not 0.0 <= hurst_value <= 1.0:
        raise ValueError("hurst debe estar dentro de [0, 1].")

    trend_strength = abs(hurst_value - 0.5) * 2.0
    elliptic_score = min(1.0, abs(ratio_value) / 5.0)
    reduction_factor = 1.0 - (elliptic_score * 0.5)
    return float(max(0.0, min(1.0, trend_strength * reduction_factor)))
