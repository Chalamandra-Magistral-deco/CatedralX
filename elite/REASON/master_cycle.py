"""Synthetic Chalamandra Core integration across existing vectors.

Uses SCX diagnostics, a non-authoritative DSX cognitive gate, MSX provenance
and optional read-only FEX feedback evaluation. This is not the production
market-data loop, independent acceptance verifier, or executor.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from DSX.DEFENSE.guards import cognitive_execution_guard
from MSX.provenance import aggregate_cycle, build_provenance

from REASON.cognitive_state import counterevidence, pairwise_coherence
from REASON.core_contract import build_cycle
from REASON.fex_feedback_adapter import evaluate_ledger


def _parse_observed_at(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("observed_at debe ser ISO-8601 con zona horaria.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("observed_at debe ser ISO-8601 válido.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("observed_at debe incluir zona horaria.")
    return parsed


def run_synthetic_master_cycle(
    *,
    cycle_id: str,
    signals: list[dict[str, Any]],
    requested_decision: str = "HOLD",
    context_ref: str = "synthetic-context",
    uncertainty: float | None = None,
    prediction: dict[str, Any] | None = None,
    outcome: dict[str, Any] | None = None,
    panic: bool = False,
    fex_feedback_path: str | Path | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Run a synthetic, non-executing cycle.

    An explicit observed_at makes the cycle timestamp and MSX event IDs
    reproducible. Without it, the current UTC time is used. Source authenticity
    is not established by this adapter, so source_status remains "unknown".

    DSX cognitive approval is diagnostic only. Independent acceptance is
    deliberately marked as not provided; this adapter has no independent
    verifier and therefore cannot satisfy that contract boundary.

    FEX is evaluated only for an explicitly supplied ledger path. Evaluation
    is read-only: this function never records predictions/outcomes or trains.
    """
    if not isinstance(signals, list) or any(not isinstance(item, dict) for item in signals):
        raise ValueError("signals debe ser una lista de objetos.")
    if not isinstance(requested_decision, str) or requested_decision.strip().upper() not in {
        "BUY", "SELL", "HOLD"
    }:
        raise ValueError("requested_decision debe ser BUY, SELL o HOLD.")
    if not isinstance(panic, bool):
        raise ValueError("panic debe ser booleano.")

    observed = _parse_observed_at(observed_at)
    timestamp = observed.isoformat()
    event_timestamp = int(observed.timestamp())

    coherence = pairwise_coherence(signals)
    opposing = counterevidence(requested_decision, signals)
    dsx = cognitive_execution_guard(coherence, opposing, panic=panic)

    # A cognitive gate is not an independent acceptance artifact.
    dsx_gate = {
        "status": "approved" if dsx["allowed"] else "veto",
        "independent": False,
        "acceptance_status": "not_provided",
        "cognitive_gate_status": "approved" if dsx["allowed"] else "blocked",
        "enforcement_vector": dsx["enforcement_vector"],
        "reasons": list(dsx["reasons"]),
        "evidence_status": coherence["evidence_status"],
        "counterevidence_status": opposing["evidence_status"],
    }

    records = [
        build_provenance(
            name="perception",
            module="SCX.pairwise_coherence",
            version="existing",
            inputs={"signals": signals},
            output=coherence,
            status=coherence["evidence_status"],
            vector="SCX",
            timestamp=event_timestamp,
        ),
        build_provenance(
            name="counterevidence",
            module="SCX.counterevidence",
            version="existing",
            inputs={"requested_decision": requested_decision, "signals": signals},
            output=opposing,
            status=opposing["evidence_status"],
            vector="SCX",
            timestamp=event_timestamp,
        ),
        build_provenance(
            name="cognitive_safety_gate",
            module="DSX.cognitive_execution_guard",
            version="existing",
            inputs={"coherence": coherence, "counterevidence": opposing, "panic": panic},
            output=dsx_gate,
            status="blocked" if dsx["blocked"] else "cognitive_approval_only",
            vector="DSX",
            timestamp=event_timestamp,
        ),
    ]

    fex_report = None
    if fex_feedback_path is not None:
        fex_report = evaluate_ledger(path=fex_feedback_path)
        records.append(build_provenance(
            name="feedback_evaluation",
            module="FEX.FEEDBACK.feedback_loop.evaluar_feedback",
            version="existing",
            inputs={"ledger_path_explicit": True},
            output={
                "report_status": fex_report.get("report_status", "unknown"),
                "predictions_recorded": fex_report.get("predictions_recorded", 0),
                "outcomes_scored": fex_report.get("outcomes_scored", 0),
                "automatic_retraining": False,
                "trading_enabled": False,
                "orders_executed": False,
            },
            status=fex_report.get("report_status", "unknown"),
            vector="FEX",
            timestamp=event_timestamp,
        ))

    # No source authentication is performed here. "unknown" prevents this
    # synthetic adapter from asserting that caller-provided signals are valid.
    result = build_cycle(
        cycle_id=cycle_id,
        observed_at=timestamp,
        source_status="unknown",
        context_ref=context_ref,
        signals=signals,
        uncertainty=uncertainty,
        prediction=dict(prediction or {}),
        regulation={"state": "review" if dsx["blocked"] else "normal"},
        decision=requested_decision.strip().upper(),
        risk_gate=dsx_gate,
        outcome=outcome,
        mode="PAPER",
    )

    records.append(build_provenance(
        name="synthetic_cycle_result",
        module="REASON.core_contract.build_cycle",
        version=result["schema_version"],
        inputs={
            "cycle_id": cycle_id,
            "observed_at": timestamp,
            "input_sha256": result["provenance"]["input_sha256"],
        },
        output={
            "decision": result["decision"],
            "action": result["action"],
            "source_status": result["source_status"],
            "record_sha256": result["provenance"]["record_sha256"],
        },
        status="intent_only" if result["action"]["status"] == "intent_only" else "blocked",
        vector="MSX",
        timestamp=event_timestamp,
    ))

    trace = aggregate_cycle(cycle_id, records)
    result["diagnostics"] = {
        "coherence": coherence,
        "counterevidence": opposing,
        "dsx": dsx,
        "independent_acceptance": {
            "status": "not_provided",
            "verified": False,
            "required_for_non_hold_decision": True,
        },
        "trace": trace,
        "fex_feedback": fex_report,
    }
    return result
