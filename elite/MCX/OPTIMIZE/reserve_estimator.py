"""
Reserve estimator. Configured rate is a planning assumption, not tax advice.
Chalamandra Magistral DecoX · CatedralX

Calcula una reserva estimada a partir de un ingreso
y una tasa de asignación configurable.
"""
from __future__ import annotations

import math
from typing import Any


def _validar_numero(nombre: str, valor: Any) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise TypeError(f"{nombre} must be an int or float, not bool")

    try:
        resultado = float(valor)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} must be a finite number") from exc

    if not math.isfinite(resultado):
        raise ValueError(f"{nombre} must be finite")

    return resultado


def estimar_reserva(ingreso: float, tasa: float = 0.02) -> dict[str, Any]:
    ingreso = _validar_numero("ingreso", ingreso)
    tasa = _validar_numero("tasa", tasa)

    if ingreso < 0:
        raise ValueError("ingreso must be >= 0")

    if not 0 <= tasa <= 1:
        raise ValueError("tasa must be between 0 and 1")

    return {
        "ingreso": round(ingreso, 2),
        "tasa_configurada": tasa,
        "reserva_estimada": round(ingreso * tasa, 2),
        "disclaimer": (
            "Estimación configurable; no determina "
            "la obligación fiscal real."
        ),
    }
