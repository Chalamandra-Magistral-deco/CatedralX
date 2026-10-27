"""Regla Central de la Catedral: Veto + Ponderación restringida.

Especificación (DECISIONS.md, Fase 1):
  - Veto Evidencia: si Evidencia < 0.85 → BLOCKED_UNCERTAINTY
  - Veto Reinversión: si Reinversión <= 0.0 → BLOCKED_DEFICIT
  - Score = 0.35*Viab + 0.25*Res + 0.20*Hum + 0.20*Dist
  - Score >= 0.70 → ACCEPTED
  - Score < 0.70 → REJECTED
"""
from __future__ import annotations
from typing import Any, Dict


EVIDENCE_MIN = 0.85
REINVESTMENT_MIN = 0.0
SCORE_MIN = 0.70
W_VIABILITY = 0.35
W_RESILIENCE = 0.25
W_HUMAN = 0.20
W_DISTRIBUTION = 0.20


def _clamp01(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    return max(0.0, min(1.0, f))


class CathedralEvaluation:
    def __init__(
        self,
        viability: float,
        human_value: float,
        distribution: float,
        reinvestment: float,
        resilience: float,
        evidence: float,
    ):
        self.dimensions = {
            "viability": _clamp01(viability),
            "human_value": _clamp01(human_value),
            "distribution": _clamp01(distribution),
            "reinvestment": float(reinvestment) if reinvestment is not None else 0.0,
            "resilience": _clamp01(resilience),
            "evidence": _clamp01(evidence),
        }

    def evaluate(self) -> Dict[str, Any]:
        # Compuerta 1: Evidencia
        if self.dimensions["evidence"] < EVIDENCE_MIN:
            return {
                "status": "BLOCKED_UNCERTAINTY",
                "score": 0.0,
                "reason": "EVIDENCIA_INSUFICIENTE",
                "next_action": "RECOLECTAR_MAS_DATOS",
                "dimensions": dict(self.dimensions),
            }

        # Compuerta 2: Reinversión
        if self.dimensions["reinvestment"] <= REINVESTMENT_MIN:
            return {
                "status": "BLOCKED_DEFICIT",
                "score": 0.0,
                "reason": "SIN_EXCEDENTE_PARA_REINVERSION",
                "next_action": "REVISAR_SOSTENIBILIDAD",
                "dimensions": dict(self.dimensions),
            }

        # Score compuesto
        score = (
            W_VIABILITY * self.dimensions["viability"]
            + W_RESILIENCE * self.dimensions["resilience"]
            + W_HUMAN * self.dimensions["human_value"]
            + W_DISTRIBUTION * self.dimensions["distribution"]
        )

        if score >= SCORE_MIN:
            return {
                "status": "ACCEPTED",
                "score": round(score, 4),
                "reason": "CUMPLE_TODOS_LOS_CRITERIOS",
                "next_action": "PUBLICAR_O_EJECUTAR",
                "dimensions": dict(self.dimensions),
            }

        return {
            "status": "REJECTED",
            "score": round(score, 4),
            "reason": "BAJO_RENDIMIENTO_GLOBAL",
            "next_action": "DESCARTAR",
            "dimensions": dict(self.dimensions),
        }
