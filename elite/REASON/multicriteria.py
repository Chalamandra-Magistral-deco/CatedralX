"""Deterministic central rule: hard vetoes + integer basis-point weighting."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any

EVIDENCE_MIN_BP = 8500
REINVESTMENT_MIN_BP = 0
SCORE_MIN_BP = 7000
W_VIABILITY_BP = 3500
W_RESILIENCE_BP = 2500
W_HUMAN_BP = 2000
W_DISTRIBUTION_BP = 2000


def _basis_points(value: Any) -> int | None:
    """Accept only an exact built-in integer in the closed range [0, 10000]."""
    if type(value) is not int or not 0 <= value <= 10000:
        return None
    return value


def _decimal(value: Any) -> Decimal | None:
    """Parse finite financial input through decimal text; never substitute a default."""
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return parsed if parsed.is_finite() else None


def _decimal_text(value: Decimal) -> str:
    """Represent exact monetary/reinvestment input as a stable non-exponent string."""
    return format(value.normalize(), "f")


def _attach_evaluation_hash(result: dict[str, Any]) -> dict[str, Any]:
    """Hash the canonical result and policy, including all block reasons."""
    canonical = {
        "schema_version": 2,
        "policy": {
            "score_scale": "integer_basis_points",
            "score_range_bp": [0, 10000],
            "evidence_min_bp": EVIDENCE_MIN_BP,
            "reinvestment_min_bp": REINVESTMENT_MIN_BP,
            "score_min_bp": SCORE_MIN_BP,
            "weights_bp": {
                "viability": W_VIABILITY_BP,
                "resilience": W_RESILIENCE_BP,
                "human_value": W_HUMAN_BP,
                "distribution": W_DISTRIBUTION_BP,
            },
        },
        "result": result,
    }
    payload = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    result["evaluation_hash"] = hashlib.sha256(payload).hexdigest()
    return result


def blocked_uncertainty(
    *,
    reason: str,
    next_action: str = "REVISAR_LOGS",
    blocking_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """Build a hashed, non-accepted result when central evaluation itself fails."""
    return _attach_evaluation_hash({
        "status": "BLOCKED_UNCERTAINTY",
        "score": 0,
        "reason": reason,
        "next_action": next_action,
        "blocking_reasons": sorted({str(item) for item in (blocking_reasons or [])}),
        "invalid_inputs": [],
        "dimensions": {},
    })


class CathedralEvaluation:
    """Evaluate explicit integer-BP dimensions and exact reinvestment surplus."""

    def __init__(
        self,
        viability: Any,
        human_value: Any,
        distribution: Any,
        reinvestment: Any,
        resilience: Any,
        evidence: Any,
    ) -> None:
        raw_scores = {
            "viability": viability,
            "human_value": human_value,
            "distribution": distribution,
            "resilience": resilience,
            "evidence": evidence,
        }
        self._invalid_inputs: list[str] = []
        scores: dict[str, int | None] = {}
        for name, value in raw_scores.items():
            scores[name] = _basis_points(value)
            if scores[name] is None:
                self._invalid_inputs.append(name)

        self._reinvestment_value = _decimal(reinvestment)
        if self._reinvestment_value is None:
            self._invalid_inputs.append("reinvestment")

        self.dimensions: dict[str, int | str | None] = {
            **scores,
            "reinvestment": (
                _decimal_text(self._reinvestment_value)
                if self._reinvestment_value is not None else None
            ),
        }

    def evaluate(self, *, blocking_reasons: list[str] | None = None) -> dict[str, Any]:
        reasons = sorted({str(reason) for reason in (blocking_reasons or []) if str(reason)})
        if reasons:
            return _attach_evaluation_hash({
                "status": "BLOCKED_UNCERTAINTY",
                "score": 0,
                "reason": "GOBERNANZA_NO_VERIFICADA",
                "next_action": "RECOLECTAR_METRICAS_VERIFICABLES",
                "blocking_reasons": reasons,
                "invalid_inputs": sorted(self._invalid_inputs),
                "dimensions": dict(self.dimensions),
            })

        if self._invalid_inputs:
            return _attach_evaluation_hash({
                "status": "BLOCKED_UNCERTAINTY",
                "score": 0,
                "reason": "ENTRADAS_CUANTITATIVAS_INVALIDAS_O_FALTANTES",
                "next_action": "VALIDAR_DATOS_Y_ESCALA_BP",
                "invalid_inputs": sorted(self._invalid_inputs),
                "blocking_reasons": [],
                "dimensions": dict(self.dimensions),
            })

        # Revalidate mutable dimensions before using them in the score.
        required_scores = (
            "viability", "human_value", "distribution", "resilience", "evidence"
        )
        validated_scores: dict[str, int] = {}
        invalid_score_dimensions: list[str] = []

        for name in required_scores:
            value = _basis_points(self.dimensions.get(name))
            if value is None:
                invalid_score_dimensions.append(name)
            else:
                validated_scores[name] = value

        if invalid_score_dimensions:
            return _attach_evaluation_hash({
                "status": "BLOCKED_UNCERTAINTY",
                "score": 0,
                "reason": "ENTRADAS_CUANTITATIVAS_INVALIDAS_O_FALTANTES",
                "next_action": "VALIDAR_DATOS_Y_ESCALA_BP",
                "invalid_inputs": sorted(invalid_score_dimensions),
                "blocking_reasons": [],
                "dimensions": dict(self.dimensions),
            })

        evidence_bp = validated_scores["evidence"]
        if evidence_bp < EVIDENCE_MIN_BP:
            return _attach_evaluation_hash({
                "status": "BLOCKED_EVIDENCE",
                "score": 0,
                "reason": "EVIDENCIA_INSUFICIENTE",
                "next_action": "RECOLECTAR_MAS_DATOS",
                "blocking_reasons": [],
                "dimensions": dict(self.dimensions),
            })

        # The surplus is a finite Decimal; no inferred default is permitted.
        reinvestment_value = self._reinvestment_value
        if reinvestment_value is None:
            return _attach_evaluation_hash({
                "status": "BLOCKED_UNCERTAINTY",
                "score": 0,
                "reason": "ENTRADAS_CUANTITATIVAS_INVALIDAS_O_FALTANTES",
                "next_action": "VALIDAR_DATOS_Y_ESCALA_BP",
                "invalid_inputs": ["reinvestment"],
                "blocking_reasons": [],
                "dimensions": dict(self.dimensions),
            })

        if reinvestment_value <= Decimal(REINVESTMENT_MIN_BP):
            return _attach_evaluation_hash({
                "status": "BLOCKED_DEFICIT",
                "score": 0,
                "reason": "SIN_EXCEDENTE_PARA_REINVERSION",
                "next_action": "REVISAR_SOSTENIBILIDAD",
                "blocking_reasons": [],
                "dimensions": dict(self.dimensions),
            })

        score = (
            W_VIABILITY_BP * validated_scores["viability"]
            + W_RESILIENCE_BP * validated_scores["resilience"]
            + W_HUMAN_BP * validated_scores["human_value"]
            + W_DISTRIBUTION_BP * validated_scores["distribution"]
        ) // 10000

        if score >= SCORE_MIN_BP:
            return _attach_evaluation_hash({
                "status": "ACCEPTED",
                "score": int(score),
                "reason": "CUMPLE_TODOS_LOS_CRITERIOS",
                "next_action": "SOLICITAR_ACEPTACION_INDEPENDIENTE",
                "blocking_reasons": [],
                "dimensions": dict(self.dimensions),
            })

        return _attach_evaluation_hash({
            "status": "REJECTED",
            "score": int(score),
            "reason": "BAJO_RENDIMIENTO_GLOBAL",
            "next_action": "DESCARTAR",
            "blocking_reasons": [],
            "dimensions": dict(self.dimensions),
        })
