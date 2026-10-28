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


EVIDENCE_MIN_BP = 8500
REINVESTMENT_MIN_BP = 0
SCORE_MIN_BP = 7000
W_VIABILITY_BP = 3500
W_RESILIENCE_BP = 2500
W_HUMAN_BP = 2000
W_DISTRIBUTION_BP = 2000


def _clamp_bp(v: Any, default: int = 0) -> int:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    return max(0, min(10000, int(round(f * 10000))))


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
            "viability": _clamp_bp(viability),
            "human_value": _clamp_bp(human_value),
            "distribution": _clamp_bp(distribution),
            "reinvestment": float(reinvestment) if reinvestment is not None else 0.0,
            "resilience": _clamp_bp(resilience),
            "evidence": _clamp_bp(evidence),
        }

    def evaluate(self) -> Dict[str, Any]:
        # Compuerta 1: Evidencia
        if self.dimensions["evidence"] < EVIDENCE_MIN_BP:
            return {
                "status": "BLOCKED_UNCERTAINTY",
                "score": 0.0,
                "reason": "EVIDENCIA_INSUFICIENTE",
                "next_action": "RECOLECTAR_MAS_DATOS",
                "dimensions": dict(self.dimensions),
            }

        # Compuerta 2: Reinversión
        if self.dimensions["reinvestment"] <= REINVESTMENT_MIN_BP:
            return {
                "status": "BLOCKED_DEFICIT",
                "score": 0.0,
                "reason": "SIN_EXCEDENTE_PARA_REINVERSION",
                "next_action": "REVISAR_SOSTENIBILIDAD",
                "dimensions": dict(self.dimensions),
            }

        # Score compuesto
        score = (
            (W_VIABILITY_BP * self.dimensions["viability"]
            + W_RESILIENCE_BP * self.dimensions["resilience"]
            + W_HUMAN_BP * self.dimensions["human_value"]
            + W_DISTRIBUTION_BP * self.dimensions["distribution"]) // 10000
        )

        if score >= SCORE_MIN_BP:
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
