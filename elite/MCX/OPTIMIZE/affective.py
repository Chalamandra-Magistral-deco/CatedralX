"""Deterministic synthetic affective profile; not a biological measurement or decision policy."""
from __future__ import annotations

import math
from typing import Any


_AFFECTIVE_DEFAULTS = {
    "oxitocina_O": 0.5,
    "dopamina_D": 0.5,
    "serotonina_S": 0.5,
    "cortisol_C": 0.3,
    "adrenalina_A": 0.4,
    "melatonina_M": 0.2,
}


def _normalized_concentration(name: str, value: Any) -> float:
    """Accept only finite real numeric concentrations in the normalized [0, 1] domain."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} debe ser un número real normalizado entre 0 y 1")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{name} debe ser finito y estar entre 0 y 1")
    return numeric


def estado_afectivo(concentraciones: dict[str, Any]) -> dict[str, Any]:
    """Return a descriptive synthetic profile from normalized internal concentrations.

    The coefficients and labels are heuristic and uncalibrated. The result is
    observability metadata only: it must not gate, recommend, or authorize actions.
    Missing concentration keys use documented defaults; supplied invalid values
    fail closed. Unknown keys are ignored to preserve forward compatibility.
    """
    if not isinstance(concentraciones, dict):
        raise ValueError("concentraciones debe ser un diccionario")

    values = {
        name: _normalized_concentration(name, concentraciones.get(name, default))
        for name, default in _AFFECTIVE_DEFAULTS.items()
    }
    oxytocin = values["oxitocina_O"]
    dopamine = values["dopamina_D"]
    serotonin = values["serotonina_S"]
    cortisol = values["cortisol_C"]
    adrenaline = values["adrenalina_A"]
    melatonin = values["melatonina_M"]

    activation = round(adrenaline * 0.6 + cortisol * 0.35 + dopamine * 0.05, 4)
    valence = round(
        oxytocin * 0.4 + serotonin * 0.4 + dopamine * 0.2 - cortisol * 0.2, 4
    )
    valence = max(-1.0, min(1.0, valence))

    calm = round(
        serotonin * 0.35 + oxytocin * 0.35 + melatonin * 0.3
        - adrenaline * 0.25 - cortisol * 0.15,
        4,
    )
    calm = max(-1.0, min(1.0, calm))

    if cortisol > 0.7 and adrenaline > 0.7:
        state = "ALERTA_MÁXIMA"
    elif cortisol > 0.5 and adrenaline > 0.5:
        state = "TENSIÓN"
    elif dopamine > 0.7 and cortisol < 0.3:
        state = "CONFIANZA"
    elif serotonin > 0.7 and cortisol < 0.35 and abs(adrenaline - 0.4) < 0.2:
        state = "ESTABILIDAD"
    elif melatonin > 0.5 and cortisol < 0.3:
        state = "RECUPERACIÓN"
    elif valence < -0.3 and activation > 0.5:
        state = "PRECAUCIÓN"
    elif valence < -0.4:
        state = "RESERVA"
    else:
        state = "NEUTRO"

    intensity = round((abs(valence) + abs(activation)) / 2.0, 4)
    return {
        "estado": state,
        "activacion": activation,
        "valencia": valence,
        "calma": calm,
        "intensidad": intensity,
        "perfil": perfil_texto(state),
        "modelo": "heuristico_sintetico_no_calibrado",
        "rol": "observacional_no_autoritativo",
        "decision_authority": False,
    }


def perfil_texto(etiqueta: str) -> str:
    """Describe the synthetic label without giving operational or financial advice."""
    descriptions = {
        "ALERTA_MÁXIMA": "Perfil sintético de activación elevada y tensión elevada.",
        "TENSIÓN": "Perfil sintético de activación y tensión moderadamente elevadas.",
        "CONFIANZA": "Perfil sintético de valencia positiva y activación relativamente baja.",
        "ESTABILIDAD": "Perfil sintético de valencia positiva y activación moderada.",
        "RECUPERACIÓN": "Perfil sintético de activación baja con predominio relativo de melatonina.",
        "PRECAUCIÓN": "Perfil sintético de valencia negativa y activación elevada.",
        "RESERVA": "Perfil sintético de valencia negativa.",
        "NEUTRO": "Perfil sintético sin predominio marcado en las dimensiones calculadas.",
    }
    return descriptions.get(etiqueta, "Perfil sintético desconocido.")


def actualizar_estado(cortisol: float = 0.3, dopamina: float = 0.5, sorpresa: float = 0.0,
                      volatilidad: float = 0.0) -> dict[str, float]:
    """Preserve the existing MCX bounded-state API."""
    values = [cortisol, dopamina, sorpresa, volatilidad]
    if any(isinstance(value, bool) for value in values):
        raise ValueError("affective inputs must be finite real numbers")
    try:
        numeric = [float(value) for value in values]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("affective inputs must be finite real numbers") from exc
    if not all(math.isfinite(value) for value in numeric):
        raise ValueError("affective inputs must be finite")
    cortisol_value, dopamine_value, surprise_value, volatility_value = numeric
    risk = min(1.0, max(0.0, abs(surprise_value) * 0.25 + abs(volatility_value) * 5.0))
    c = min(1.0, max(0.0, 0.7 * cortisol_value + 0.3 * risk))
    d = min(1.0, max(0.0, 0.8 * dopamine_value + 0.2 * (1.0 - risk)))
    return {
        "cortisol": round(c, 6),
        "dopamina": round(d, 6),
        "serotonina": round(min(1.0, max(0.0, 1.0 - risk * 0.5)), 6),
        "riesgo_estimado": round(risk, 6),
    }
