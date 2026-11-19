"""Homeostasis, regulación y primitivas de decisión para la capa MCX.

Este módulo calcula límites y recomendaciones de análisis. No autoriza,
crea ni ejecuta órdenes; la autorización permanece en las capas superiores.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def _bounded(value: Any, name: str, default: float) -> float:
    """Convierte un valor a float finito y lo limita al intervalo [0, 1]."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} debe ser numérico") from exc
    if not np.isfinite(number):
        raise ValueError(f"{name} debe ser finito")
    return float(np.clip(number, 0.0, 1.0))


# ---------------------------------------------------------------------
# Capa 1 — Seguridad básica
# ---------------------------------------------------------------------

def umbrales_seguridad(
    neuro: dict[str, float], panic: bool = False
) -> dict[str, Any]:
    """Evalúa el estado defensivo antes de calcular cualquier sensibilidad."""
    cortisol = _bounded(
        neuro.get("cortisol_C", neuro.get("cortisol", 1.0)),
        "cortisol",
        1.0,
    )
    dopamina = _bounded(
        neuro.get("dopamina_D", neuro.get("dopamina", 0.0)),
        "dopamina",
        0.0,
    )
    defensivo = bool(panic) or cortisol >= 0.7

    return {
        "modo_base": "DEFENSIVO" if defensivo else "NORMAL",
        "agresividad_base": (
            0.0 if defensivo else round(dopamina * (1.0 - cortisol), 4)
        ),
        "umbral_minimo": (
            1.0 if defensivo else round(0.4 + cortisol * 0.4, 4)
        ),
        "operaciones_permitidas": not defensivo,
        # Compatibilidad: MCX nunca concede permiso para ejecutar órdenes.
        "orders_allowed": False,
    }


def parametros_homeostaticos(
    neuro: dict[str, float], panic: bool = False
) -> dict[str, Any]:
    """Mantiene la interfaz histórica consumida por MCX y sus pruebas."""
    base = umbrales_seguridad(neuro, panic)
    return {
        "modo": base["modo_base"],
        "agresividad": base["agresividad_base"],
        "umbral_minimo": base["umbral_minimo"],
        "orders_allowed": False,
    }


# ---------------------------------------------------------------------
# Capa 2 — Sensibilidad homeostática
# ---------------------------------------------------------------------

def calcular_beta(
    dopamina: float,
    cortisol: float,
    serotonina: float,
    volatilidad: float,
    gap_norm: float,
) -> float:
    """Calcula sensibilidad acotada; más riesgo de mercado reduce beta."""
    d = _bounded(dopamina, "dopamina", 0.5)
    c = _bounded(cortisol, "cortisol", 0.3)
    s = _bounded(serotonina, "serotonina", 0.5)
    vol = float(volatilidad)
    gap = float(gap_norm)
    if not np.isfinite(vol) or vol < 0.0:
        raise ValueError("volatilidad debe ser finita y no negativa")
    if not np.isfinite(gap):
        raise ValueError("gap_norm debe ser finito")

    riesgo = (vol / 100.0) + (abs(gap) / 50.0)
    beta = (d / (c + 0.2)) * (1.0 / (1.0 + riesgo))
    beta *= 0.5 + s * 0.5
    return float(np.clip(beta, 0.1, 5.0))


# ---------------------------------------------------------------------
# Capa 3 — Aprendizaje y decisión
# ---------------------------------------------------------------------

def softmax(q_values: list[float], beta: float) -> list[float]:
    """Convierte valores Q en probabilidades con estabilidad numérica."""
    q = np.asarray(q_values, dtype=float)
    if q.size == 0:
        return []
    if not np.all(np.isfinite(q)):
        raise ValueError("q_values debe contener únicamente valores finitos")
    temperature = float(beta)
    if not np.isfinite(temperature) or temperature <= 0.0:
        raise ValueError("beta debe ser finita y mayor que cero")

    shifted = q - np.max(q)
    exponentials = np.exp(temperature * shifted)
    probabilities = exponentials / np.sum(exponentials)
    return probabilities.tolist()


def q_learning_actualizar(
    q_actual: float,
    recompensa: float,
    max_q_futuro: float,
    alpha: float = 0.1,
    gamma: float = 0.95,
) -> float:
    """Actualiza Q-learning y limita el resultado al intervalo [-1, 1]."""
    values = np.asarray(
        [q_actual, recompensa, max_q_futuro, alpha, gamma], dtype=float
    )
    if not np.all(np.isfinite(values)):
        raise ValueError("Los parámetros de Q-learning deben ser finitos")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha debe pertenecer a [0, 1]")
    if not 0.0 <= gamma <= 1.0:
        raise ValueError("gamma debe pertenecer a [0, 1]")

    nuevo_q = q_actual + alpha * (
        recompensa + gamma * max_q_futuro - q_actual
    )
    return float(np.clip(nuevo_q, -1.0, 1.0))


def tamaño_posicion_optimo(
    rendimientos: list[float],
    perdida_max_aceptada: float = 0.1,
) -> float:
    """Busca por rejilla una fracción acotada que maximiza log-crecimiento.

    Es una estimación heurística sobre los rendimientos suministrados; no es
    una implementación completa de Kelly ni sustituye límites de capital,
    liquidez, exposición o autorización externos.
    """
    if not rendimientos:
        return 0.02

    perdida = float(perdida_max_aceptada)
    if not np.isfinite(perdida) or perdida <= 0.0:
        raise ValueError("perdida_max_aceptada debe ser finita y positiva")

    returns = np.asarray(rendimientos, dtype=float)
    if returns.ndim != 1 or not np.all(np.isfinite(returns)):
        raise ValueError("rendimientos debe ser una lista unidimensional finita")

    mejor_fraccion = 0.02
    mejor_crecimiento = -np.inf
    for fraccion in np.linspace(0.01, 0.5, 20):
        factores = 1.0 + fraccion * returns / perdida
        if np.any(factores <= 0.0):
            continue
        crecimiento = float(np.sum(np.log(factores)))
        if crecimiento > mejor_crecimiento:
            mejor_crecimiento = crecimiento
            mejor_fraccion = float(fraccion)

    return round(mejor_fraccion, 4)


# ---------------------------------------------------------------------
# Capa 4 — Control homeostático
# ---------------------------------------------------------------------

def homeostasis_lqr(
    estado: np.ndarray,
    q_matrix: np.ndarray | float,
    r_matrix: np.ndarray | float,
) -> tuple[float, float]:
    """Calcula una ganancia escalar tipo LQR y una señal proporcional.

    Esta primitiva usa K = Q / (Q + R) para escalares positivos. No resuelve
    la ecuación algebraica de Riccati ni reemplaza un controlador LQR completo.
    """
    state = np.asarray(estado, dtype=float)
    q_value = np.asarray(q_matrix, dtype=float)
    r_value = np.asarray(r_matrix, dtype=float)

    if state.size == 0 or not np.all(np.isfinite(state)):
        raise ValueError("estado debe contener valores finitos")
    if q_value.size != 1 or r_value.size != 1:
        raise ValueError("q_matrix y r_matrix deben ser escalares en esta primitiva")

    q = float(q_value.reshape(-1)[0])
    r = float(r_value.reshape(-1)[0])
    if not np.isfinite(q) or not np.isfinite(r) or q < 0.0 or r < 0.0:
        raise ValueError("Q y R deben ser finitos y no negativos")
    if q + r == 0.0:
        raise ValueError("Q y R no pueden ser ambos cero")

    ganancia = q / (q + r)
    señal_control = -ganancia * float(state.reshape(-1)[0])
    return float(ganancia), float(señal_control)


# ---------------------------------------------------------------------
# Estado unificado para el orquestador
# ---------------------------------------------------------------------

def estado_homeostatico(
    hormonas: dict[str, float],
    mercado: dict[str, float],
    panic: bool = False,
) -> dict[str, Any]:
    """Combina seguridad y sensibilidad sin conceder autorización de trading."""
    base = umbrales_seguridad(hormonas, panic)

    if base["modo_base"] == "DEFENSIVO":
        beta = 0.1
        modo = "DEFENSIVO"
        sensibilidad = 0.9091
    else:
        beta = calcular_beta(
            hormonas.get("dopamina_D", hormonas.get("dopamina", 0.5)),
            hormonas.get("cortisol_C", hormonas.get("cortisol", 0.3)),
            hormonas.get("serotonina_S", hormonas.get("serotonina", 0.5)),
            mercado.get("volatilidad", 0.01),
            mercado.get("gap", 0.0),
        )
        modo = (
            "AGRESIVO" if beta > 1.5
            else "CONSERVADOR" if beta < 0.5
            else "EQUILIBRADO"
        )
        sensibilidad = round(1.0 / (1.0 + beta), 4)

    return {
        **base,
        "modo": base["modo_base"],
        "agresividad": base["agresividad_base"],
        "beta_precision": round(beta, 4),
        "modo_operativo": modo,
        "sensibilidad": sensibilidad,
        # El modo recomendado no es permiso de ejecución.
        "orders_allowed": False,
    }
