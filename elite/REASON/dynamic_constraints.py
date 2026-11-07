"""Fail-closed hard constraints for the CatedralX dynamic loop.

This module evaluates governance constraints only. It does not allocate money,
create orders, or infer missing calibration values.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, TypeGuard


@dataclass(frozen=True)
class DynamicConstraintInputs:
    reinvestment_surplus: float | None = None
    entropy_rate: float | None = None
    entropy_time_scale: float | None = None
    loop_gain: float | None = None
    dominant_signal_weight: float | None = None
    minimum_confidence: float | None = None
    signal_count: int | None = None
    optimal_signal_count: int | None = None
    exposure: float | None = None
    max_exposure: float | None = None
    resilience: float | None = None
    minimum_resilience: float | None = None
    degradation_rate: float | None = None
    accumulated_noise: float | None = None


def _finite(value: float | None) -> TypeGuard[float]:
    return value is not None and not isinstance(value, bool) and math.isfinite(float(value))


def evaluate_dynamic_constraints(inputs: DynamicConstraintInputs) -> dict[str, Any]:
    """Evaluate only calibrated constraints; missing metrics never authorize growth.

    Entropy gate: B >= T * dS/dt. Loop stability: G < 1. Scale gate:
    N <= N*; E <= E_max; resilience >= R_min.
    """
    required = (
        "reinvestment_surplus", "entropy_rate", "entropy_time_scale", "loop_gain",
        "signal_count", "optimal_signal_count", "exposure", "max_exposure",
        "resilience", "minimum_resilience",
    )
    values = asdict(inputs)
    missing = [name for name in required if values[name] is None]
    invalid = [
        name for name, value in values.items()
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        )
    ]
    # Signal counts are discrete, non-negative quantities: never truncate floats.
    for name in ("signal_count", "optimal_signal_count"):
        value = values[name]
        if value is not None and (type(value) is not int or value < 0) and name not in invalid:
            invalid.append(name)

    # Domain validation: finite numbers are not automatically meaningful numbers.
    # Ratios are bounded; magnitudes and time scales cannot be negative.
    lower_bounds = {
        "reinvestment_surplus": 0.0,
        "entropy_rate": 0.0,
        "entropy_time_scale": 0.0,
        "loop_gain": 0.0,
        "exposure": 0.0,
        "max_exposure": 0.0,
        "resilience": 0.0,
        "minimum_resilience": 0.0,
        "degradation_rate": 0.0,
        "accumulated_noise": 0.0,
        "dominant_signal_weight": 0.0,
        "minimum_confidence": 0.0,
    }
    for name, minimum in lower_bounds.items():
        value = values[name]
        if value is not None and name not in invalid and float(value) < minimum:
            invalid.append(name)
    if values["entropy_time_scale"] is not None and values["entropy_time_scale"] == 0 and "entropy_time_scale" not in invalid:
        invalid.append("entropy_time_scale")

    for name in ("dominant_signal_weight", "minimum_confidence", "resilience", "minimum_resilience"):
        value = values[name]
        if value is not None and name not in invalid and float(value) > 1.0:
            invalid.append(name)

    issues = []
    if invalid:
        issues.append("DATOS_INVALIDOS")
    if missing:
        issues.append("METRICAS_NO_CALIBRADAS")

    entropy_ok = False
    feedback_ok = False
    scale_ok = False
    if not invalid and not missing:
        # Defensa en profundidad: missing/invalid ya garantizan no-None y finitos.
        # Los asserts documentan el invariante para mypy y fallan rápido si la
        # validación previa se rompe.
        assert inputs.reinvestment_surplus is not None
        assert inputs.entropy_time_scale is not None
        assert inputs.entropy_rate is not None
        assert inputs.loop_gain is not None
        assert inputs.signal_count is not None
        assert inputs.optimal_signal_count is not None
        assert inputs.exposure is not None
        assert inputs.max_exposure is not None
        assert inputs.resilience is not None
        assert inputs.minimum_resilience is not None
        entropy_ok = float(inputs.reinvestment_surplus) >= float(inputs.entropy_time_scale) * float(inputs.entropy_rate)
        feedback_ok = float(inputs.loop_gain) < 1.0
        scale_ok = (
            inputs.signal_count <= inputs.optimal_signal_count
            and float(inputs.exposure) <= float(inputs.max_exposure)
            and float(inputs.resilience) >= float(inputs.minimum_resilience)
        )
        if not entropy_ok:
            issues.append("MANTENIMIENTO_ENTROPICO")
        if not feedback_ok:
            issues.append("FRENO_DINAMICO")
        if not scale_ok:
            issues.append("MODULARIZAR_O_REDUCIR_EXPOSICION")

    # Missing/invalid metrics block growth but are distinguished from measured breaches.
    growth_allowed = not invalid and not missing and entropy_ok and feedback_ok and scale_ok
    state = "CRECIMIENTO_PERMITIDO" if growth_allowed else (
        "MANTENIMIENTO" if "MANTENIMIENTO_ENTROPICO" in issues else
        "FRENO_DINAMICO" if "FRENO_DINAMICO" in issues else
        "MODULARIZAR" if "MODULARIZAR_O_REDUCIR_EXPOSICION" in issues else
        "RESTRICCIONES_NO_VERIFICADAS"
    )
    return {
        "state": state,
        "growth_allowed": growth_allowed,
        "entropy_constraint_ok": entropy_ok,
        "feedback_constraint_ok": feedback_ok,
        "scale_constraint_ok": scale_ok,
        "issues": issues,
        "missing_metrics": missing,
        "invalid_metrics": invalid,
        "degradation_rate_observed": inputs.degradation_rate,
        "accumulated_noise_observed": inputs.accumulated_noise,
        "automatic_recalibration": False,
        "automatic_modularization": False,
    }
