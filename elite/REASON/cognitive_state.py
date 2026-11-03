# AUDITOR APPROVAL 2026-10-25: integrado como CAMINO B bajo firma del Auditor.
# Originalmente marcado provisional en AUDITORIA_CONSOLIDACION_PERGAMINO.md.
# Aprobado explícitamente por el Auditor (autor del Pergamino) el 2026-10-25.

"""Evidence-aware cognitive state helpers for the CatedralX reasoning vector (SCX).

Pure functions only: no network, persistence, model training, or financial execution.
Unknown evidence stays unknown; heuristic strength is never relabeled as probability.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any, TypeGuard

SCHEMA_VERSION = "4.2-cognitive-draft"
DIRECTIONS = {"buy": 1, "compra": 1, "bullish": 1, "alcista": 1,
              "sell": -1, "venta": -1, "bearish": -1, "bajista": -1,
              "hold": 0, "lateral": 0, "neutral": 0, "flat": 0}


def _finite(value: Any) -> TypeGuard[float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _direction(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and _finite(value):
        return 1 if value > 0 else -1 if value < 0 else 0
    if isinstance(value, str):
        return DIRECTIONS.get(value.strip().lower())
    return None


def pairwise_coherence(signals: Iterable[dict[str, Any]], weights: dict[str, float] | None = None) -> dict[str, Any]:
    """Compute weighted pairwise directional agreement for explicit, confident signals.

    Each signal needs name, direction, confidence in [0,1]. Invalid/incomplete
    signals are excluded and reported; no confidence is inferred from indicator values.
    """
    weights = weights or {}
    valid: list[dict[str, Any]] = []
    rejected: list[str] = []
    for index, item in enumerate(signals):
        name = str(item.get("name", f"signal_{index}"))
        direction = _direction(item.get("direction"))
        confidence = item.get("confidence")
        if direction is None or not _finite(confidence) or not 0 <= float(confidence) <= 1:
            rejected.append(name)
            continue
        valid.append({"name": name, "direction": direction, "confidence": float(confidence)})
    numerator = 0.0
    denominator = 0.0
    pairs = []
    for i, left in enumerate(valid):
        for right in valid[i + 1:]:
            key = f"{left['name']}|{right['name']}"
            weight = weights.get(key, weights.get(f"{right['name']}|{left['name']}", 1.0))
            if not _finite(weight) or float(weight) <= 0:
                continue
            weight = float(weight)
            if left["direction"] == 0 or right["direction"] == 0:
                # Neutral signals are recorded but do not count as evidence of agreement
                # or contradiction. Otherwise HOLD would manufacture dissonance.
                pairs.append({"pair": [left["name"], right["name"]], "agreement": 0.0,
                              "weight": weight, "status": "neutral_not_scored"})
                continue
            agreement = left["confidence"] * right["confidence"]
            if left["direction"] != right["direction"]:
                agreement *= -1.0
            numerator += weight * agreement
            denominator += weight
            pairs.append({"pair": [left["name"], right["name"]], "agreement": round(agreement, 6), "weight": weight, "status": "scored"})
    coherence = numerator / denominator if denominator else None
    dissonance = (1.0 - coherence) / 2.0 if coherence is not None else None
    consensus = ("ALTO" if coherence > 0.75 else "MEDIO" if coherence > 0.45 else "BAJO") if coherence is not None else "NO_EVALUABLE"
    return {"coherencia": round(coherence, 6) if coherence is not None else None,
            "disonancia": round(dissonance, 6) if dissonance is not None else None,
            "consenso_cualitativo": consensus, "pares": pairs,
            "senales_validas": len(valid), "senales_excluidas": rejected,
            "evidence_status": "computed" if denominator else "insufficient_evidence",
            "dissonance_threshold_exceeded": bool(dissonance is not None and dissonance > 0.40)}


def counterevidence(decision: Any, signals: Iterable[dict[str, Any]], abort_threshold: float = 0.35) -> dict[str, Any]:
    """Summarize explicitly supplied opposing evidence; never invent missing signals."""
    if not _finite(abort_threshold) or not 0 <= float(abort_threshold) <= 1:
        raise ValueError("abort_threshold debe estar entre 0 y 1")
    target = _direction(decision)
    opposing: list[dict[str, Any]] = []
    total = 0.0
    if target not in (-1, 1):
        return {"senales_opuestas": [], "fuerza_contra": None, "umbral_abortar": float(abort_threshold),
                "decision_sobrevive": None, "evidence_status": "non_directional_decision"}
    for item in signals:
        direction = _direction(item.get("direction"))
        confidence = item.get("confidence")
        weight = item.get("weight", 1.0)
        if direction not in (-1, 1) or direction == target or not _finite(confidence) or not _finite(weight):
            continue
        if not 0 <= float(confidence) <= 1 or float(weight) < 0:
            continue
        strength = float(confidence) * float(weight)
        total += strength
        opposing.append({"name": str(item.get("name", "unknown")), "direction": direction,
                         "confidence": float(confidence), "weight": float(weight), "weighted_strength": round(strength, 6)})
    # Normalize to [0,1] so threshold is interpretable; weight mass is explicit.
    force = total / sum(x["weight"] for x in opposing) if opposing and sum(x["weight"] for x in opposing) else 0.0
    return {"senales_opuestas": opposing, "fuerza_contra": round(force, 6),
            "umbral_abortar": float(abort_threshold), "decision_sobrevive": force <= float(abort_threshold),
            "evidence_status": "computed" if opposing else "no_opposing_signal_observed"}


def uncertainty(epistemic_sigma: float | None, aleatoric_sigma: float | None) -> dict[str, Any]:
    """Combine two non-negative standard-deviation estimates when both are known."""
    if not _finite(epistemic_sigma) or not _finite(aleatoric_sigma) or epistemic_sigma < 0 or aleatoric_sigma < 0:
        return {"u_total": None, "evidence_status": "uncertainty_components_unavailable"}
    return {"u_total": round(math.sqrt(float(epistemic_sigma) ** 2 + float(aleatoric_sigma) ** 2), 8),
            "evidence_status": "computed"}


def metacognition(*, coherence: dict[str, Any], epistemic_sigma: float | None = None,
                  aleatoric_sigma: float | None = None, confidence: float | None = None,
                  historical_accuracy: float | None = None, error_slope: float | None = None,
                  epsilon: float = 1e-3, weights: tuple[float, float, float, float] = (1, 1, 1, 1)) -> dict[str, Any]:
    """Report observability and risk; does not call heuristic strength calibrated confidence."""
    u = uncertainty(epistemic_sigma, aleatoric_sigma)
    dissonance = coherence.get("disonancia")
    gap = abs(float(confidence) - float(historical_accuracy)) if _finite(confidence) and _finite(historical_accuracy) and 0 <= confidence <= 1 and 0 <= historical_accuracy <= 1 else None
    if not _finite(error_slope):
        learning = "NO_EVALUABLE"
    elif error_slope < -abs(epsilon):
        learning = "mejorando"
    elif error_slope > abs(epsilon):
        learning = "degradando"
    else:
        learning = "estable"
    w1, w2, w3, w4 = weights
    u_total = u.get("u_total")
    if _finite(dissonance) and _finite(u_total) and _finite(gap) and _finite(historical_accuracy):
        assert dissonance is not None
        assert u_total is not None
        assert gap is not None
        assert historical_accuracy is not None
        z = w1 * float(dissonance) + w2 * float(u_total) + w3 * float(gap) - w4 * float(historical_accuracy)
        z = max(-60.0, min(60.0, z))
        chaos = 1.0 / (1.0 + math.exp(-z))
    else:
        chaos = None
    return {"incertidumbre": u["u_total"], "incertidumbre_status": u["evidence_status"],
            "disonancia": dissonance, "confianza_historica": historical_accuracy,
            "brecha_calibracion": gap, "aprendizaje": learning, "riesgo_caos": round(chaos, 6) if chaos is not None else None,
            "needs_review": bool((gap is not None and gap > 0.15) or (chaos is not None and chaos > 0.35) or (dissonance is not None and dissonance > 0.40)),
            "calibration_status": "diagnostic_gap_only_not_brier_or_ece" if gap is not None else "insufficient_labeled_history"}


def regime_context(history: Iterable[str], alpha: float = 1.0, max_history: int = 100) -> dict[str, Any]:
    """Laplace-smoothed Markov context from explicitly observed regime labels."""
    if not _finite(alpha) or alpha <= 0 or not isinstance(max_history, int) or max_history < 2:
        raise ValueError("alpha debe ser positivo y max_history >= 2")
    labels = [x for x in history if isinstance(x, str) and x.strip()][-max_history:]
    regimes = sorted(set(labels))
    if len(labels) < 2 or not regimes:
        return {"fase_actual": labels[-1] if labels else None, "fase_anterior": labels[-2] if len(labels) > 1 else None,
                "transicion": f"{labels[-2]}→{labels[-1]}" if len(labels) > 1 else None,
                "tiempo_en_regimen": None, "P_salida": None, "entropia_contexto_nats": None,
                "historial_fases": labels, "transition_counts": {}, "transition_probabilities": {},
                "evidence_status": "insufficient_regime_history"}
    counts = {a: {b: 0 for b in regimes} for a in regimes}
    for a, b in zip(labels, labels[1:]):
        counts[a][b] += 1
    probs = {}
    for a in regimes:
        denom = sum(counts[a].values()) + alpha * len(regimes)
        probs[a] = {b: (counts[a][b] + alpha) / denom for b in regimes}
    current = labels[-1]
    row = probs[current]
    entropy = -sum(p * math.log(p) for p in row.values() if p > 0)
    duration = 0
    for label in reversed(labels):
        if label != current:
            break
        duration += 1
    return {"fase_actual": current, "fase_anterior": labels[-2], "transicion": f"{labels[-2]}→{current}",
            "tiempo_en_regimen": duration, "P_salida": round(1.0 - row[current], 8),
            "entropia_contexto_nats": round(entropy, 8), "historial_fases": labels,
            "transition_counts": counts, "transition_probabilities": probs,
            "evidence_status": "computed_from_observed_labels"}






