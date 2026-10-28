"""Regla central determinista de CatedralX: vetos + ponderación en basis points.

Los scores se normalizan a enteros en [0, 10000]. No se realiza aritmética
IEEE-754: valores decimales heredados se convierten mediante Decimal(str(v));
los enteros se interpretan directamente como basis points.
"""
from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

EVIDENCE_MIN_BP = 8500
REINVESTMENT_MIN_BP = 0
SCORE_MIN_BP = 7000
W_VIABILITY_BP = 3500
W_RESILIENCE_BP = 2500
W_HUMAN_BP = 2000
W_DISTRIBUTION_BP = 2000


def _decimal(value: Any, default: Decimal = Decimal(0)) -> Decimal:
    """Parse a finite decimal without performing binary floating-point arithmetic."""
    if isinstance(value, bool) or value is None:
        return default
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default
    return parsed if parsed.is_finite() else default


def _clamp_bp(value: Any, default: int = 0) -> int:
    """Return an integer basis-point score, clamped to [0, 10000].

    Built-in integers are already basis points. Non-integer numeric inputs keep
    backward compatibility with the legacy normalized [0,1] contract but are
    converted through decimal text, never used in floating-point calculations.
    """
    if isinstance(value, bool) or value is None:
        return default
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default
    if not decimal_value.is_finite():
        return default
    scaled = decimal_value if isinstance(value, int) else decimal_value * Decimal(10000)
    rounded = int(scaled.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return max(0, min(10000, rounded))


def _decimal_text(value: Decimal) -> str:
    """Represent exact monetary/reinvestment input as a stable non-exponent string."""
    normalized = value.normalize()
    return format(normalized, "f")


def _attach_evaluation_hash(result: dict[str, Any]) -> dict[str, Any]:
    """Hash the canonical result and policy; exclude the hash field itself."""
    canonical = {
        "schema_version": 1,
        "policy": {
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


class CathedralEvaluation:
    """Evaluate a proposal with integer-BP scores and exact reinvestment comparison."""

    def __init__(
        self,
        viability: Any,
        human_value: Any,
        distribution: Any,
        reinvestment: Any,
        resilience: Any,
        evidence: Any,
    ) -> None:
        reinvestment_value = _decimal(reinvestment)
        self._reinvestment_value = reinvestment_value
        self.dimensions = {
            "viability": _clamp_bp(viability),
            "human_value": _clamp_bp(human_value),
            "distribution": _clamp_bp(distribution),
            "reinvestment": _decimal_text(reinvestment_value),
            "resilience": _clamp_bp(resilience),
            "evidence": _clamp_bp(evidence),
        }

    def evaluate(self) -> dict[str, Any]:
        # Gate 1: minimum evidence. Integer comparison only.
        if self.dimensions["evidence"] < EVIDENCE_MIN_BP:
            return _attach_evaluation_hash({
                "status": "BLOCKED_EVIDENCE",
                "score": 0,
                "reason": "EVIDENCIA_INSUFICIENTE",
                "next_action": "RECOLECTAR_MAS_DATOS",
                "dimensions": dict(self.dimensions),
            })

        # Gate 2: a positive reinvestment surplus is required; comparison is Decimal-exact.
        if self._reinvestment_value <= Decimal(REINVESTMENT_MIN_BP):
            return _attach_evaluation_hash({
                "status": "BLOCKED_REINVERSION",
                "score": 0,
                "reason": "SIN_EXCEDENTE_PARA_REINVERSION",
                "next_action": "REVISAR_SOSTENIBILIDAD",
                "dimensions": dict(self.dimensions),
            })

        # Weighted sum is an integer in basis points; no IEEE-754 operation occurs.
        score = (
            W_VIABILITY_BP * self.dimensions["viability"]
            + W_RESILIENCE_BP * self.dimensions["resilience"]
            + W_HUMAN_BP * self.dimensions["human_value"]
            + W_DISTRIBUTION_BP * self.dimensions["distribution"]
        ) // 10000

        if score >= SCORE_MIN_BP:
            return _attach_evaluation_hash({
                "status": "ACCEPTED",
                "score": int(score),
                "reason": "CUMPLE_TODOS_LOS_CRITERIOS",
                "next_action": "PUBLICAR_O_EJECUTAR",
                "dimensions": dict(self.dimensions),
            })

        return _attach_evaluation_hash({
            "status": "REJECTED",
            "score": int(score),
            "reason": "BAJO_RENDIMIENTO_GLOBAL",
            "next_action": "DESCARTAR",
            "dimensions": dict(self.dimensions),
        })
