"""
homeostasis_lqr.py — Linear-Quadratic Regulator for internal state stabilization
Chalamandra Magistral DecoX · CatedralX

Lleva el estado interno hacia el punto de referencia de forma óptima,
minimizando tanto el desvío como el esfuerzo de corrección.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class StateWeights:
    """Pesos de importancia para cada variable del vector de estado."""
    cortisol: float = 2.0
    dopamina: float = 1.0
    serotonina: float = 1.0
    riesgo: float = 3.0


@dataclass
class ControlWeights:
    """Costo de aplicar corrección a cada variable."""
    ajuste_cortisol: float = 0.5
    ajuste_dopamina: float = 0.8
    ajuste_serotonina: float = 0.8


@dataclass
class Setpoint:
    """Estado objetivo al que el sistema tiende a volver."""
    cortisol: float = 0.3
    dopamina: float = 0.6
    serotonina: float = 0.7
    riesgo: float = 0.25


def lqr_correction(
    actual: dict[str, float],
    target: Setpoint | None = None,
    q: StateWeights | None = None,
    r: ControlWeights | None = None,
) -> dict[str, float]:
    """
    Calcula la corrección ponderada óptima para acercar el estado
    actual al estado de referencia, minimizando el costo total:
    
        J = Σ [xᵀ·Q·x + uᵀ·R·u]
    
    Donde:
        x = desvío respecto al objetivo
        u = corrección aplicada
        Q = penalización por desvío
        R = costo de corrección
    """
    t = target or Setpoint()
    qw = q or StateWeights()
    rw = r or ControlWeights()

    # Desvío del estado respecto al objetivo
    dx = {
        "cortisol": actual.get("cortisol", 0.3) - t.cortisol,
        "dopamina": actual.get("dopamina", 0.5) - t.dopamina,
        "serotonina": actual.get("serotonina", 0.5) - t.serotonina,
        "riesgo": actual.get("riesgo_estimado", 0.5) - t.riesgo,
    }

    # Ley de control: u = −K·x  →  K = R⁻¹·Bᵀ·P (simplificada para homeostasis)
    # Corrección ponderada: mayor peso en variables críticas, menor esfuerzo costoso
    correccion = {
        "cortisol": -(qw.cortisol / rw.ajuste_cortisol) * dx["cortisol"],
        "dopamina": -(qw.dopamina / rw.ajuste_dopamina) * dx["dopamina"],
        "serotonina": -(qw.serotonina / rw.ajuste_serotonina) * dx["serotonina"],
    }

    # Estado corregido, acotado en [0, 1]
    nuevo = {
        "cortisol": max(0.0, min(1.0, actual["cortisol"] + correccion["cortisol"])),
        "dopamina": max(0.0, min(1.0, actual["dopamina"] + correccion["dopamina"])),
        "serotonina": max(0.0, min(1.0, actual["serotonina"] + correccion["serotonina"])),
        "riesgo_estimado": actual.get("riesgo_estimado", 0.5),
    }

    return {
        "desvio": {k: round(v, 6) for k, v in dx.items()},
        "correccion_aplicada": {k: round(v, 6) for k, v in correccion.items()},
        "estado_anterior": actual,
        "estado_nuevo": nuevo,
        "estabilizado": all(abs(dx[k]) < 0.01 for k in correccion),
    }


def decay_gain(cycles: int, base_gain: float = 0.25, half_life: int = 96) -> float:
    """
    Atenúa gradualmente la fuerza de corrección para evitar oscilaciones.
    Decaimiento: g = g₀ × 0.5^(ciclos / vida_media)
    """
    if cycles < 0:
        raise ValueError("Ciclos no puede ser negativo")
    return base_gain * (0.5 ** (cycles / half_life))
