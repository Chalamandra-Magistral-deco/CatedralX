"""
Bounded deterministic internal state; not a biological measurement.
Chalamandra Magistral DecoX · CatedralX

Calcula el perfil interno del sistema a partir de:
  - cortisol: nivel de incertidumbre/acumulación de estrés
  - dopamina: refuerzo / confianza en la señal
  - sorpresa: desviación respecto a lo esperado (energía libre)
  - volatilidad: ruido del mercado / inestabilidad local
"""
from __future__ import annotations

import math


def actualizar_estado(
    cortisol: float = 0.3,
    dopamina: float = 0.5,
    sorpresa: float = 0.0,
    volatilidad: float = 0.0,
) -> dict[str, float]:
    values = [cortisol, dopamina, sorpresa, volatilidad]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("affective inputs must be finite")

    cortisol = float(cortisol)
    dopamina = float(dopamina)
    sorpresa = float(sorpresa)
    volatilidad = float(volatilidad)

    # Riesgo combinado: sorpresa + volatilidad
    riesgo = min(1.0, max(0.0, abs(sorpresa) * 0.25 + abs(volatilidad) * 5.0))

    # Hormonas derivadas, acotadas en [0, 1]
    c = min(1.0, max(0.0, 0.7 * cortisol + 0.3 * riesgo))
    d = min(1.0, max(0.0, 0.8 * dopamina + 0.2 * (1.0 - riesgo)))
    s = min(1.0, max(0.0, 1.0 - riesgo * 0.5))

    return {
        "cortisol": round(c, 6),
        "dopamina": round(d, 6),
        "serotonina": round(s, 6),
        "riesgo_estimado": round(riesgo, 6),
    }
