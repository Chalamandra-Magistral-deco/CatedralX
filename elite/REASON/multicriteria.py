"""Regla Central de la Catedral: Evaluación Multicriterio (6 dimensiones)."""
from __future__ import annotations
from typing import Dict, Any

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
            "viability": viability,
            "human_value": human_value,
            "distribution": distribution,
            "reinvestment": reinvestment,
            "resilience": resilience,
            "evidence": evidence,
        }
        self.conflicts = []

    def evaluate(self) -> Dict[str, Any]:
        # 1. Veto de Evidencia (Fail-Closed)
        if self.dimensions["evidence"] < 0.5:
            return {
                "status": "REJECTED",
                "score": 0.0,
                "reason": "EVIDENCIA_INSUFICIENTE",
                "next_action": "RECOLECTAR_MAS_DATOS",
                "conflicts": ["Falta de evidencia confiable"],
            }

        # 2. Veto de Resiliencia
        if self.dimensions["resilience"] < 0.4:
            return {
                "status": "UNCERTAIN",
                "score": 0.0,
                "reason": "SISTEMA_FRAGIL",
                "next_action": "REVISION_MANUAL_DE_RIESGO",
                "conflicts": ["Resiliencia por debajo del umbral mínimo"],
            }

        # 3. Detección de Conflicto de Valores
        if self.dimensions["viability"] > 0.8 and self.dimensions["human_value"] < 0.3:
            return {
                "status": "UNCERTAIN",
                "score": 0.0,
                "reason": "CONFLICTO_DE_VALORES",
                "next_action": "REVISION_ETICA",
                "conflicts": ["Alta viabilidad económica pero bajo valor humano"],
            }

        # 4. Cálculo del Score (Regla Central)
        score = (
            self.dimensions["viability"] * 0.30 +
            self.dimensions["human_value"] * 0.20 +
            self.dimensions["distribution"] * 0.15 +
            self.dimensions["reinvestment"] * 0.20 +
            self.dimensions["resilience"] * 0.15
        )

        # 5. Decisión Final
        if score >= 0.75:
            return {
                "status": "ACCEPTED",
                "score": round(score, 4),
                "reason": "CUMPLE_TODOS_LOS_CRITERIOS",
                "next_action": "PUBLICAR_O_EJECUTAR",
                "conflicts": [],
            }
        else:
            return {
                "status": "REJECTED",
                "score": round(score, 4),
                "reason": "SCORE_POR_DEBAJO_DEL_UMBRAL",
                "next_action": "DESCARTAR",
                "conflicts": ["Score total insuficiente"],
            }
