"""
homeostasis_lqr.py — Linear-Quadratic Regulator for state stabilization
Chalamandra Magistral DecoX · CatedralX

Calcula la corrección óptima para regresar al equilibrio sin oscilar en exceso.
"""
from __future__ import annotations

def lqr_correction(
    actual: dict[str, float],
    target: dict[str, float],
    q_weights: dict[str, float] | None = None,
    r_weights: dict[str, float] | None = None,
) -> dict:
    """
    u = −K·x  —  atrae suavemente el estado hacia el objetivo
    sin aplicar más fuerza que la necesaria.
    """
    q = q_weights or {"cortisol": 2.0, "dopamina": 1.0, "serotonina": 1.0, "riesgo": 3.0}
    r = r_weights or {"cortisol": 0.5, "dopamina": 0.8, "serotonina": 0.8}

    dx = {k: actual.get(k, 0.0) - target.get(k, 0.3) for k in q}
    correccion = {k: -(q[k] / r.get(k, 1.0)) * dx[k] for k in q if k in r}

    nuevo = {
        k: max(0.0, min(1.0, actual[k] + correccion[k]))
        for k in correccion
    }
    return {
        "desvio": {k: round(v, 6) for k, v in dx.items()},
        "correccion_aplicada": {k: round(v, 6) for k, v in correccion.items()},
        "estado_nuevo": nuevo,
        "estabilizado": all(abs(dx[k]) < 0.01 for k in correccion),
    }

def decay_gain(cycles: int, base_gain: float = 0.25, half_life: int = 96) -> float:
    """Atenúa la corrección con el tiempo para evitar rebotes."""
    if cycles < 0:
        raise ValueError("Ciclos no puede ser negativo")
    return round(base_gain * (0.5 ** (cycles / half_life)), 6)
