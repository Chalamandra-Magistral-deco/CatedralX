"""DecisionResult builder for CatedralX with central-governor provenance."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_EVALUATION_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def build_decision_result(
    state: Any,
    cognitive: dict[str, Any],
    cycle_id: str | int | None = None,
    *,
    trace_id: str | None = None,
) -> dict[str, Any]:
    perception = getattr(state, "percepcion_espacial", {}) or {}
    trace_candidate = trace_id or cognitive.get("trace_id") or perception.get("trace_id")
    if not isinstance(trace_candidate, str) or not _TRACE_ID_RE.fullmatch(trace_candidate) or trace_candidate == "0" * 32:
        trace_candidate = uuid.uuid4().hex

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

    prov_records = cognitive.get("provenance", [])
    if isinstance(prov_records, dict) and "records" in prov_records:
        prov_records = prov_records["records"]

    evidence = []
    prov_ids = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in prov_records:
        if not isinstance(item, dict):
            continue
        prov_ids.append(item.get("id", ""))
        evidence.append({
            "evidence_id": item.get("id", str(uuid.uuid4())),
            "kind": "calculation",
            "source": item.get("module", "unknown"),
            "observed_at": now_iso,
            "digest": item.get("hash"),
            "notes": item.get("status", ""),
        })

    risks = perception.get("analisis_financiero", {}).get("risk_flags", [])
    resolved_cycle_id = cycle_id if cycle_id is not None else perception.get("cycle_id")
    return {
        "result_id": str(uuid.uuid4()),
        "status": status,
        "engine": "CatedralX",
        "decision": getattr(state, "decision", "HOLD"),
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
