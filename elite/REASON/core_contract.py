"""Chalamandra Core v1: deterministic, synthetic, non-executing master cycle.

This module is additive and deliberately does not call exchanges, brokers, order
writers, network services, or persistent state paths. DSX is represented by an
explicit independent gate result; a missing/invalid gate fails closed.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from datetime import datetime
from typing import Any, TypeGuard

SCHEMA_VERSION = "chalamandra-core/1.0"
MODES = {"RESEARCH", "BACKTEST", "PAPER", "LIVE"}
LIVE_DEFAULT_ENABLED = False


def _finite_number(value: Any) -> TypeGuard[float]:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False, default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_cycle(
    *,
    cycle_id: str,
    observed_at: str,
    source_status: str,
    context_ref: str | None,
    signals: list[dict[str, Any]],
    uncertainty: float | None,
    prediction: Mapping[str, Any],
    regulation: Mapping[str, Any] | None = None,
    decision: str = "HOLD",
    risk_gate: Mapping[str, Any] | None = None,
    outcome: Mapping[str, Any] | None = None,
    mode: str = "RESEARCH",
) -> dict[str, Any]:
    """Build a validated cycle record. No action is executed."""
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id requerido")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("observed_at requerido")
    try:
        parsed_observed_at = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at debe ser ISO-8601") from exc
    if parsed_observed_at.tzinfo is None or parsed_observed_at.utcoffset() is None:
        raise ValueError("observed_at debe incluir zona horaria")
    if source_status not in {"valid", "degraded", "invalid", "unknown"}:
        raise ValueError("source_status inválido")
    if mode not in MODES:
        raise ValueError("mode inválido")
    if not isinstance(decision, str) or decision.strip().upper() not in {"BUY", "SELL", "HOLD"}:
        raise ValueError("decision debe ser BUY, SELL o HOLD")
    if not isinstance(signals, list) or any(not isinstance(x, dict) for x in signals):
        raise ValueError("signals debe ser una lista de objetos")
    if uncertainty is not None and (
        not _finite_number(uncertainty) or float(uncertainty) < 0
    ):
        raise ValueError("uncertainty debe ser un número finito no negativo o None")
    if not isinstance(prediction, Mapping):
        raise ValueError("prediction debe ser un objeto")
    if outcome is not None and not isinstance(outcome, Mapping):
        raise ValueError("outcome debe ser un objeto o None")

    gate = dict(risk_gate or {})
    gate_approved = gate.get("status") == "approved" and gate.get("independent") is True
    data_usable = source_status == "valid"
    # This module never authorizes LIVE. Even an approved gate yields intent only.
    if not data_usable or not gate_approved or mode == "LIVE":
        final_decision = "HOLD"
        action = {"status": "blocked", "executable": False, "reason":
                  "invalid_data" if not data_usable else
                  "live_disabled" if mode == "LIVE" else "risk_gate_not_approved"}
    else:
        final_decision = decision.strip().upper()
        action = {"status": "intent_only", "executable": False,
                  "reason": "synthetic_cycle_no_execution"}

    predicted = prediction.get("value")
    observed = outcome.get("value") if outcome is not None else None
    if outcome is not None and _finite_number(predicted) and _finite_number(observed):
        prediction_error = {
            "value": round(float(observed) - float(predicted), 12),
            "status": "computed_from_observed_outcome",
        }
    else:
        prediction_error = {"value": None, "status": "awaiting_observed_outcome"}

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "cycle_id": cycle_id,
        "observed_at": observed_at,
        "source_status": source_status,
        "context_ref": context_ref,
        "signals": [dict(x) for x in signals],
        "uncertainty": float(uncertainty) if uncertainty is not None else None,
        "prediction": dict(prediction),
        "prediction_error": prediction_error,
        "regulation": dict(regulation or {}),
        "decision": {"requested": decision.strip().upper(), "final": final_decision},
        "risk_gate": gate,
        "action": action,
        "outcome": dict(outcome) if outcome is not None else None,
        "provenance": {"input_sha256": _digest({
            "cycle_id": cycle_id, "observed_at": observed_at,
            "source_status": source_status, "context_ref": context_ref,
            "signals": signals, "uncertainty": uncertainty,
            "prediction": dict(prediction), "mode": mode,
        })},
        "mode": mode,
    }
    payload["provenance"]["record_sha256"] = _digest(payload)
    return payload
