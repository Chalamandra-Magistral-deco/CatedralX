"""
homeostasis.py — Internal state reference targets
Chalamandra Magistral DecoX · CatedralX

Define los puntos de equilibrio saludable del sistema.
"""
from __future__ import annotations

def setpoint() -> dict[str, float]:
    """Estado de referencia al que el sistema tiende a volver."""
    return {
        "cortisol": 0.3,
        "dopamina": 0.6,
        "serotonina": 0.7,
        "riesgo": 0.25,
    }

def desvio(actual: dict[str, float], objetivo: dict[str, float] | None = None) -> dict[str, float]:
    """Diferencia entre estado actual y el objetivo."""
    t = objetivo or setpoint()
    return {k: round(actual.get(k, 0.0) - t[k], 6) for k in t}
