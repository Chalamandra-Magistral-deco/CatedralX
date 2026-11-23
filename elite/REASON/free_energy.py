"""Predictive-discrepancy score used by the reasoning cycle.

This bounded heuristic is not physical energy or a full variational free-energy
objective. It compares a bounded trend prediction with observed market inputs.
"""
import math


def _finite(name: str, value: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} debe ser un número finito")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser un número finito") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} debe ser un número finito")
    return result


def free_energy(
    prediccion_tendencia: float,
    realidad_gap: float,
    inercia_observada: float,
    retorno_actual: float = 0.0,
    coherencia_previa: float = 0.5,
) -> float:
    """Calculate bounded surprise from a prediction and observed market data.

    This remains a legacy heuristic, not a calibrated probability or physical
    energy measure. The prediction and coherence inputs are bounded explicitly.
    """
    prediction = _finite("prediccion_tendencia", prediccion_tendencia)
    gap = _finite("realidad_gap", realidad_gap)
    inertia = _finite("inercia_observada", inercia_observada)
    observed_return = _finite("retorno_actual", retorno_actual)
    coherence = _finite("coherencia_previa", coherencia_previa)
    if not 0.0 <= prediction <= 1.0:
        raise ValueError("prediccion_tendencia debe estar entre 0 y 1")
    if gap < 0.0:
        raise ValueError("realidad_gap no puede ser negativo")
    if not 0.0 <= coherence <= 1.0:
        raise ValueError("coherencia_previa debe estar entre 0 y 1")

    fe_base = abs(observed_return) * 10.0
    error_gap = min(1.0, gap * 200.0)
    inercia_esperada = 2.0 * (prediction - 0.5)
    error_inercia = min(1.0, abs(inertia - inercia_esperada) / 2.0)
    factor_decoherencia = 1.0 + (1.0 - coherence)
    fe_total = (fe_base + error_gap + error_inercia) * factor_decoherencia * 2.5
    return float(min(20.0, max(0.0, fe_total)))


def prediccion_interna(hurst: float, cross_ratio: float) -> float:
    """Estimate continuation pressure from bounded Hurst and cross-ratio inputs."""
    hurst_value = _finite("hurst", hurst)
    ratio_value = _finite("cross_ratio", cross_ratio)
    if not 0.0 <= hurst_value <= 1.0:
        raise ValueError("hurst debe estar entre 0 y 1")
    fuerza_tendencia = abs(hurst_value - 0.5) * 2.0
    score_eliptico = min(1.0, abs(ratio_value) / 5.0)
    factor_reduccion = 1.0 - (score_eliptico * 0.5)
    prob_tendencia = fuerza_tendencia * factor_reduccion
    return float(max(0.0, min(1.0, prob_tendencia)))