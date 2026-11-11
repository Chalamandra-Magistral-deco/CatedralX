"""DecisionResult builder for CatedralX with central-governor provenance."""
from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from .actions import normalizar_senal

_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_EVALUATION_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _extract_provenance_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []

    trace = value.get("cycle_trace")
    if isinstance(trace, dict) and isinstance(trace.get("records"), list):
        return [item for item in trace["records"] if isinstance(item, dict)]

    records = value.get("records")
    if isinstance(records, list):
        return [item for item in records if isinstance(item, dict)]

    result = []
    report = value.get("cognitive_report")
    if isinstance(report, dict):
        result.append(report)
    sources = value.get("sources")
    if isinstance(sources, dict):
        result.extend(item for item in sources.values() if isinstance(item, dict))
    return result


def _provenance_time(timestamp: Any, fallback: str) -> str:
    if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
        try:
            return datetime.fromtimestamp(float(timestamp), UTC).isoformat()
        except (OverflowError, OSError, ValueError):
            pass
    return fallback


def build_decision_result(
    state: Any,
    cognitive: dict[str, Any],
    cycle_id: str | int | None = None,
    *,
    trace_id: str | None = None,
) -> dict[str, Any]:
    perception = getattr(state, "percepcion_espacial", {}) or {}
    if trace_id is not None:
        trace_candidate = trace_id
    elif "trace_id" in cognitive:
        trace_candidate = cognitive.get("trace_id")
    else:
        trace_candidate = perception.get("trace_id")
    if trace_candidate is None:
        trace_candidate = uuid.uuid4().hex
    elif (
        not isinstance(trace_candidate, str)
        or not _TRACE_ID_RE.fullmatch(trace_candidate)
        or trace_candidate == "0" * 32
    ):
        raise ValueError("trace_id explícito inválido; se rechaza para no romper la correlación")

    verdict = cognitive.get("cathedral_verdict", {})
    if not isinstance(verdict, dict):
        verdict = {}
    raw_missing_inputs = verdict.get("invalid_inputs", [])
    missing_inputs = sorted({str(item) for item in raw_missing_inputs if str(item)}) if isinstance(raw_missing_inputs, list) else []
    raw_blocking_reasons = verdict.get("blocking_reasons", [])
    blocking_reasons = sorted({str(item) for item in raw_blocking_reasons if str(item)}) if isinstance(raw_blocking_reasons, list) else []
    evaluation_hash = verdict.get("evaluation_hash")
    if not isinstance(evaluation_hash, str) or not _EVALUATION_HASH_RE.fullmatch(evaluation_hash):
        raise ValueError("La Regla Central no proporcionó un evaluation_hash SHA-256 válido")
    else:
        gate_status = str(verdict.get("status", "UNCERTAIN"))
        if gate_status == "ACCEPTED":
            status = "ACCEPTED"
        elif gate_status == "REJECTED":
            status = "REJECTED"
        elif gate_status == "BLOCKED_UNCERTAINTY" and missing_inputs:
            # Missing required central dimensions are a distinct fail-closed state;
            # never collapse them into generic uncertainty or infer substitute values.
            status = "BLOCKED_MISSING_INPUT"
        elif gate_status in {"BLOCKED_EVIDENCE", "BLOCKED_REINVERSION", "BLOCKED_UNCERTAINTY", "BLOCKED_DEFICIT"}:
            status = "UNCERTAIN"
        else:
            status = "UNCERTAIN"

    # Diagnostics can only downgrade an accepted central verdict. They cannot
    # replace a central veto/block with another status.
    if gate_status == "ACCEPTED":
        disonancia = cognitive.get("coherencia", {}).get("disonancia", 0) or 0
        contraevidencia = cognitive.get("contraevidencia", {}).get("fuerza_contra", 0) or 0
        if disonancia > 0.8 or contraevidencia > 0.7:
            status = "REJECTED"
        elif disonancia > 0.4 or contraevidencia > 0.35:
            status = "UNCERTAIN"

    raw_decision = getattr(state, "decision", "HOLD")
    try:
        canonical_decision = normalizar_senal(raw_decision)
    except (TypeError, ValueError) as exc:
        raise ValueError("DecisionResult requiere una decisión canónica buy, sell o hold") from exc

    prov_records = _extract_provenance_records(cognitive.get("provenance", []))

    evidence = []
    prov_ids = []
    now_iso = datetime.now(UTC).isoformat()
    for item in prov_records:
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier:
            continue
        prov_ids.append(identifier)
        evidence.append({
            "evidence_id": identifier,
            "kind": "calculation",
            "source": item.get("modulo", item.get("module", "unknown")),
            "vector": item.get("vector"),
            "version": item.get("version"),
            "observed_at": _provenance_time(item.get("timestamp"), now_iso),
            "digest": item.get("input_hash") or item.get("input_hash_sha256") or item.get("hash"),
            "notes": item.get("status", ""),
        })

    if status == "ACCEPTED" and (
        not evidence
        or any(
            not isinstance(item.get("digest"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["digest"])
            or not isinstance(item.get("source"), str)
            or not item["source"].strip()
            for item in evidence
        )
    ):
        status = "UNCERTAIN"

    risks = perception.get("analisis_financiero", {}).get("risk_flags", [])
    resolved_cycle_id = cycle_id if cycle_id is not None else perception.get("cycle_id")
    return {
        "result_id": str(uuid.uuid4()),
        "status": status,
        "engine": "CatedralX",
        "decision": canonical_decision,
        "evaluation_hash": evaluation_hash,
        "evaluation_gate": gate_status,
        "missing_inputs": missing_inputs,
        "blocking_reasons": blocking_reasons,
        "evaluation_reason": verdict.get("reason"),
        "evidence": evidence,
        "assumptions": [],
        "risks": risks,
        "tests": [],
        "provenance": prov_ids,
        "trace_id": trace_candidate,
        "cycle_id": resolved_cycle_id,
        "analysis_only": True,
        "orders_created": False,
        "orders_executed": False,
        "next_action": "None" if status == "ACCEPTED" else "Manual review required",
    }
