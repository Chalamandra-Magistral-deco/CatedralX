"""Angular market state with a two-state extended Kalman filter.

The output is a heuristic diagnostic, not a physical angular measurement or
a calibrated probability. Input and carried filter state are validated before
they can influence a cycle.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Any

import numpy as np

from . import hurst_analyzer as hurst


def _finite_real(value: Any) -> bool:
    """Return True only for finite real scalars; booleans are not measurements."""
    return (
        isinstance(value, Real)
        and not isinstance(value, (bool, np.bool_))
        and math.isfinite(float(value))
    )


def _validated_prices(precios: Any) -> np.ndarray:
    """Convert a one-dimensional sequence of positive finite numeric prices."""
    if not isinstance(precios, (list, tuple, np.ndarray)):
        raise ValueError("precios debe ser una lista, tupla o arreglo unidimensional.")
    if isinstance(precios, np.ndarray) and precios.ndim != 1:
        raise ValueError("precios debe ser un arreglo unidimensional.")
    values = list(precios)
    if any(not _finite_real(value) or float(value) <= 0.0 for value in values):
        raise ValueError("Todos los precios deben ser numéricos, positivos y finitos.")
    result = np.asarray(values, dtype=np.float64)
    if result.ndim != 1 or not np.all(np.isfinite(result)):
        raise ValueError("precios debe contener únicamente valores finitos.")
    return result


def _validated_filter_state(estado_previo: Any) -> tuple[np.ndarray, np.ndarray]:
    """Validate the EKF state vector and covariance matrix."""
    if not isinstance(estado_previo, (tuple, list)) or len(estado_previo) != 2:
        raise ValueError("estado_previo debe contener (x, P).")
    try:
        x_prev = np.asarray(estado_previo[0], dtype=np.float64)
        p_prev = np.asarray(estado_previo[1], dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("El estado previo del filtro debe ser numérico.") from exc
    if x_prev.shape != (2,) or p_prev.shape != (2, 2):
        raise ValueError("El estado previo requiere x con forma (2,) y P con forma (2, 2).")
    if not np.all(np.isfinite(x_prev)) or not np.all(np.isfinite(p_prev)):
        raise ValueError("El estado previo del filtro debe ser finito.")
    if not np.allclose(p_prev, p_prev.T, rtol=1e-10, atol=1e-12):
        raise ValueError("La covarianza previa debe ser simétrica.")
    try:
        min_eigenvalue = float(np.min(np.linalg.eigvalsh(p_prev)))
    except np.linalg.LinAlgError as exc:
        raise ValueError("No se pudo validar la covarianza previa.") from exc
    if min_eigenvalue < -1e-10:
        raise ValueError("La covarianza previa debe ser semidefinida positiva.")
    return x_prev.copy(), p_prev.copy()


def extended_kalman_filter(
    omega_bruto: float,
    x_prev: np.ndarray,
    p_prev: np.ndarray,
    dt: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Estimate angular velocity and bias from a raw angular observation."""
    if not _finite_real(omega_bruto):
        raise ValueError("omega_bruto debe ser un valor real y finito.")
    if not _finite_real(dt) or float(dt) <= 0.0:
        raise ValueError("dt debe ser positivo y finito.")
    x_prev, p_prev = _validated_filter_state((x_prev, p_prev))
    dt = float(dt)

    transition = np.array([[1.0, -dt], [0.0, 1.0]])
    process_noise = np.diag([0.01, 0.001])
    x_pred = transition @ x_prev
    p_pred = transition @ p_prev @ transition.T + process_noise

    observation_matrix = np.array([[1.0, 0.0]])
    measurement_noise = np.array([[0.05]])
    innovation = np.array([float(omega_bruto)]) - observation_matrix @ x_pred
    innovation_covariance = (
        observation_matrix @ p_pred @ observation_matrix.T + measurement_noise
    )
    try:
        kalman_gain = np.linalg.solve(
            innovation_covariance, observation_matrix @ p_pred
        ).T
    except np.linalg.LinAlgError as exc:
        raise ValueError("La covarianza de innovación no es invertible.") from exc

    x_new = x_pred + kalman_gain @ innovation
    identity = np.eye(2)
    residual_transform = identity - kalman_gain @ observation_matrix
    # Joseph form preserves covariance symmetry/positivity more robustly.
    p_new = (
        residual_transform @ p_pred @ residual_transform.T
        + kalman_gain @ measurement_noise @ kalman_gain.T
    )
    p_new = (p_new + p_new.T) / 2.0
    if not np.all(np.isfinite(x_new)) or not np.all(np.isfinite(p_new)):
        raise ValueError("El filtro produjo un estado no finito.")
    return x_new, p_new, float(x_new[0])


def gyro_state(
    precios: list[float],
    estado_previo: tuple[np.ndarray, np.ndarray] | None = None,
) -> dict[str, Any]:
    """Return phase, direction, angular velocity and Hurst diagnostics."""
    values = _validated_prices(precios)
    if estado_previo is not None:
        estado_previo = _validated_filter_state(estado_previo)

    if len(values) < 10:
        return {
            "fase": "CAOS",
            "orientacion": "NEUTRO",
            "omega": 0.0,
            "precesion": 0.0,
            "estabilidad": 0.5,
            "entropia": 0.5,
            "confianza": 0.0,
            "hurst_corto": 0.5,
            "hurst_largo": 0.5,
            "_estado_filtro": None,
        }

    h_short = hurst.hurst_exponent(values[-20:], max_lag=10) if len(values) >= 20 else 0.5
    h_long = hurst.hurst_exponent(values[-60:], max_lag=30) if len(values) >= 60 else 0.5
    if not _finite_real(h_short) or not _finite_real(h_long):
        raise ValueError("Los estimadores de Hurst deben ser finitos.")
    h_short = float(h_short)
    h_long = float(h_long)
    if not 0.0 <= h_short <= 1.0 or not 0.0 <= h_long <= 1.0:
        raise ValueError("Los estimadores de Hurst deben estar en [0, 1].")

    omega_bruto = h_short - h_long
    if estado_previo is None:
        x_prev = np.array([omega_bruto, 0.0])
        p_prev = np.eye(2) * 0.1
    else:
        x_prev, p_prev = estado_previo

    x_new, p_new, omega = extended_kalman_filter(omega_bruto, x_prev, p_prev)
    omega = max(-1.0, min(1.0, omega * 2.0))

    estabilidad = min(1.0, abs(h_short - 0.5) * 2.0)
    entropia = 1.0 - estabilidad
    if h_short > 0.7:
        fase = "TENDENCIA"
    elif h_short < 0.4:
        fase = "RANGO"
    else:
        fase = "CAOS"

    recent = values[-5:]
    max_abs = float(np.max(np.abs(recent)))
    scaled_recent = recent / max_abs
    mean_abs = max_abs * float(np.mean(np.abs(scaled_recent)))
    slope_scaled = float(np.polyfit(np.arange(5), scaled_recent, 1)[0])
    normalized_slope = slope_scaled / (1.0 + 1e-9 / mean_abs)
    if normalized_slope > 0.001:
        orientacion = "ALCISTA"
    elif normalized_slope < -0.001:
        orientacion = "BAJISTA"
    else:
        orientacion = "NEUTRO"

    precesion = omega * estabilidad
    confianza = estabilidad * (1.0 - abs(omega))
    metrics = (omega, precesion, estabilidad, entropia, confianza)
    if not all(math.isfinite(value) for value in metrics):
        raise ValueError("El giroscopio produjo métricas no finitas.")
    return {
        "fase": fase,
        "orientacion": orientacion,
        "omega": float(omega),
        "precesion": float(precesion),
        "estabilidad": float(estabilidad),
        "entropia": float(entropia),
        "confianza": float(confianza),
        "hurst_corto": h_short,
        "hurst_largo": h_long,
        "_estado_filtro": (x_new, p_new),
    }
