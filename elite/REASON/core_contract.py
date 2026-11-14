"""Chalamandra Core v1: deterministic, synthetic, non-executing master cycle.

This module is additive and deliberately does not call exchanges, brokers, order
writers, network services, or persistent state paths. DSX is represented by an
explicit independent gate result; a missing/invalid gate fails closed.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
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


def compute_opportunity_evaluation_hash(result: dict[str, Any]) -> str:
    """Recompute an opportunity ``evaluation_hash`` (C-2).

    The opportunity hash is ``_digest`` of the whole result object WITHOUT
    its own ``evaluation_hash`` field. It binds every scenario, financial
    and evidence field of the evaluation, not just its format.
    """
    return _digest({key: value for key, value in result.items() if key != "evaluation_hash"})


def verify_opportunity_evaluation_hash(
    result: dict[str, Any], *, expected: str | None = None
) -> dict[str, Any]:
    """Recompute and compare an opportunity ``evaluation_hash`` (C-2).

    Same report shape as ``REASON.multicriteria.verify_evaluation_hash``;
    never raises for a bad input.
    """
    if not isinstance(result, dict):
        return {"valid": False, "kind": "opportunity", "expected": expected,
                "computed": None, "reason": "result_not_an_object"}
    embedded = result.get("evaluation_hash")
    wanted = expected if expected is not None else embedded
    if not isinstance(wanted, str) or not wanted:
        return {"valid": False, "kind": "opportunity", "expected": wanted,
                "computed": None, "reason": "missing_expected_hash"}
    try:
        computed = compute_opportunity_evaluation_hash(result)
    except (TypeError, ValueError):
        return {"valid": False, "kind": "opportunity", "expected": wanted,
                "computed": None, "reason": "unserializable_result"}
    try:
        match = hmac.compare_digest(wanted, computed)
    except (TypeError, ValueError):
        match = False
    if not match:
        return {"valid": False, "kind": "opportunity", "expected": wanted,
                "computed": computed, "reason": "hash_mismatch"}
    return {"valid": True, "kind": "opportunity", "expected": wanted,
            "computed": computed, "reason": "ok"}


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

    # "independent" is an upstream assertion, not cryptographic verification.
    # This pure builder trusts the supplied gate object; a separate acceptance
    # boundary must verify verifier identity, signature and evidence digest.
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


OPPORTUNITY_SCHEMA_VERSION = "catedralx.economic-opportunity/1.0"
_OPPORTUNITY_TRACE_RE = re.compile(r"^[0-9a-f]{32}$")
_OPPORTUNITY_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_OPPORTUNITY_SCENARIOS = {"conservative", "base", "optimistic"}
_OPPORTUNITY_FREQUENCY_MONTHS = {
    "one_time": None, "monthly": 1.0, "quarterly": 3.0, "annual": 12.0,
}


def _opportunity_number(value: Any, field: str, *, allow_zero: bool = True) -> float:
    if not _finite_number(value):
        raise ValueError(f"{field} debe ser numérico y finito.")
    number = float(value)
    if number < 0 or (not allow_zero and number == 0):
        raise ValueError(f"{field} fuera de rango.")
    return number


def _opportunity_lines(lines: Any, field: str, horizon_months: int, evidence_ids: set[str]) -> float:
    if not isinstance(lines, list) or not lines:
        raise ValueError(f"{field} requiere al menos una partida explícita.")
    total = 0.0
    for index, item in enumerate(lines):
        prefix = f"{field}[{index}]"
        if not isinstance(item, Mapping):
            raise ValueError(f"{prefix} debe ser un objeto.")
        amount = _opportunity_number(item.get("amount"), f"{prefix}.amount")
        frequency = item.get("frequency")
        if frequency not in _OPPORTUNITY_FREQUENCY_MONTHS:
            raise ValueError(f"{prefix}.frequency inválida.")
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or evidence_id not in evidence_ids:
            raise ValueError(f"{prefix}.evidence_id debe referir evidencia declarada.")
        period_months = _OPPORTUNITY_FREQUENCY_MONTHS[frequency]
        total += amount if period_months is None else amount * horizon_months / period_months
    if not math.isfinite(total):
        raise ValueError(f"{field} excede el rango numérico.")
    return total


def evaluate_economic_opportunity(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate a declared business opportunity; calculate scenarios, never execute."""
    if not isinstance(payload, Mapping):
        raise ValueError("payload debe ser un objeto.")
    required = {
        "opportunity_id", "name", "category", "income_model", "currency", "horizon_months",
        "capital_required", "available_capital", "revenue", "costs",
        "evidence", "assumptions", "scenarios", "trace_id",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError("missing_fields:" + ",".join(missing))
    for field in ("opportunity_id", "name", "category"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise ValueError(f"{field} debe ser texto no vacío.")
    income_model = payload.get("income_model")
    if income_model not in {"active", "passive", "hybrid", "investment", "asset"}:
        raise ValueError("income_model debe ser active, passive, hybrid, investment o asset.")
    currency = payload.get("currency")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency debe ser un código de moneda de tres letras en mayúsculas.")
    horizon = payload.get("horizon_months")
    if type(horizon) is not int or not 1 <= horizon <= 120:
        raise ValueError("horizon_months debe ser entero entre 1 y 120.")
    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or not _OPPORTUNITY_TRACE_RE.fullmatch(trace_id) or trace_id == "0" * 32:
        raise ValueError("trace_id W3C inválido.")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence requiere al menos una fuente declarada.")
    evidence_ids: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            raise ValueError(f"evidence[{index}] debe ser un objeto.")
        identifier, source, digest = item.get("evidence_id"), item.get("source"), item.get("digest")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in evidence_ids:
            raise ValueError(f"evidence[{index}].evidence_id inválido o duplicado.")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"evidence[{index}].source requerido.")
        if not isinstance(digest, str) or not _OPPORTUNITY_DIGEST_RE.fullmatch(digest):
            raise ValueError(f"evidence[{index}].digest debe ser SHA-256 hexadecimal.")
        observed_at = item.get("observed_at")
        if not isinstance(observed_at, str):
            raise ValueError(f"evidence[{index}].observed_at requerido.")
        try:
            parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"evidence[{index}].observed_at debe ser ISO-8601.") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(f"evidence[{index}].observed_at requiere zona horaria.")
        evidence_ids.add(identifier)
    assumptions = payload.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions or any(
        not isinstance(item, str) or not item.strip() for item in assumptions
    ):
        raise ValueError("assumptions requiere supuestos explícitos no vacíos.")
    capital_required = _opportunity_number(payload.get("capital_required"), "capital_required")
    available_capital = _opportunity_number(payload.get("available_capital"), "available_capital")
    revenue_total = _opportunity_lines(payload.get("revenue"), "revenue", horizon, evidence_ids)
    cost_total = _opportunity_lines(payload.get("costs"), "costs", horizon, evidence_ids)

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 3:
        raise ValueError("scenarios requiere exactamente conservative, base y optimistic.")
    by_name = {}
    for item in scenarios:
        if not isinstance(item, Mapping):
            raise ValueError("cada escenario debe ser un objeto.")
        name = item.get("name")
        if name not in _OPPORTUNITY_SCENARIOS or name in by_name:
            raise ValueError("escenarios duplicados o no canónicos.")
        revenue_factor = _opportunity_number(item.get("revenue_multiplier"), f"{name}.revenue_multiplier")
        cost_factor = _opportunity_number(item.get("cost_multiplier"), f"{name}.cost_multiplier")
        if revenue_factor <= 0 or cost_factor <= 0:
            raise ValueError("multiplicadores de escenario deben ser mayores que cero.")
        by_name[name] = (revenue_factor, cost_factor)
    if set(by_name) != _OPPORTUNITY_SCENARIOS:
        raise ValueError("faltan escenarios conservative, base u optimistic.")

    funding_gap = max(0.0, capital_required - available_capital)
    results = {}
    for name in ("conservative", "base", "optimistic"):
        revenue_factor, cost_factor = by_name[name]
        revenue = revenue_total * revenue_factor
        costs = cost_total * cost_factor
        net = revenue - costs
        monthly_net = net / horizon
        margin = (net / revenue * 100.0) if revenue > 0 else None
        roi = (net / capital_required * 100.0) if capital_required > 0 else None
        payback = (capital_required / monthly_net) if monthly_net > 0 and capital_required > 0 else None
        candidate = "REJECT" if net <= 0 else ("DEFER" if funding_gap > 0 else "PURSUE")
        results[name] = {
            "revenue_total": round(revenue, 2),
            "cost_total": round(costs, 2),
            "net_result": round(net, 2),
            "net_margin_pct": round(margin, 4) if margin is not None else None,
            "roi_pct": round(roi, 4) if roi is not None else None,
            "payback_months": round(payback, 2) if payback is not None else None,
            "decision_candidate": candidate,
        }
    canonical_input = json.dumps(dict(payload), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=str)
    input_hash = hashlib.sha256(canonical_input.encode("utf-8")).hexdigest()
    base = results["base"]
    risk_flags = []
    if any(row["net_result"] <= 0 for row in results.values()):
        risk_flags.append("scenario_with_non_positive_net_result")
    if funding_gap > 0:
        risk_flags.append("capital_funding_gap")
    if revenue_total <= 0:
        risk_flags.append("no_revenue_forecast")
    result = {
        "schema_version": OPPORTUNITY_SCHEMA_VERSION,
        "result_id": hashlib.sha256((input_hash + trace_id).encode()).hexdigest()[:32],
        "engine": "CatedralX",
        "evaluation_domain": "business_opportunity",
        "status": "ANALYSIS_COMPLETE",
        "opportunity_id": payload["opportunity_id"],
        "name": payload["name"],
        "category": payload["category"],
        "income_model": income_model,
        "currency": currency,
        "horizon_months": horizon,
        "financials": {
            "capital_required": round(capital_required, 2),
            "available_capital": round(available_capital, 2),
            "funding_gap": round(funding_gap, 2),
            "revenue_total_base_input": round(revenue_total, 2),
            "cost_total_base_input": round(cost_total, 2),
            "initial_capital_status": "funded" if funding_gap == 0 else "funding_gap",
            "working_capital_assessment": "not_assessed_without_periodic_cashflow",
            "tax_assessment": "not_included_unless_declared_as_cost_line",
        },
        "scenarios": results,
        "decision_candidate": base["decision_candidate"],
        "risk_flags": risk_flags,
        "assumptions": list(assumptions),
        "evidence": [dict(item) for item in evidence],
        "evidence_status": "declared_digest_not_source_authentication",
        "uncertainty": {
            "status": "not_probability_calibrated",
            "note": "Los escenarios son supuestos declarados; no son probabilidades ni predicciones calibradas.",
        },
        "provenance": {"input_sha256": input_hash},
        "trace_id": trace_id,
        "analysis_only": True,
        "orders_created": False,
        "orders_executed": False,
        "authorization": "NOT_GRANTED",
        "independent_acceptance_required": True,
    }
    result["evaluation_hash"] = _digest(result)
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Evaluación económica de oportunidades sin ejecución.")
    parser.add_argument("--input-file", required=True)
    args = parser.parse_args()
    try:
        with open(args.input_file, encoding="utf-8") as stream:
            payload = json.load(stream)
        result = evaluate_economic_opportunity(payload)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
