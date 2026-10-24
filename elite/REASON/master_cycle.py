"""Synthetic Chalamandra Core integration across existing vectors.

Uses SCX diagnostics, DSX enforcement, MSX provenance and optional read-only FEX
feedback evaluation. This is not the production market-data loop or executor.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from DSX.DEFENSE.guards import cognitive_execution_guard
from MSX.provenance import aggregate_cycle, build_provenance
from REASON.cognitive_state import counterevidence, pairwise_coherence
from REASON.core_contract import build_cycle
from REASON.fex_feedback_adapter import evaluate_ledger


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
) -> dict[str, Any]:
    """Run a reproducible cycle without writes or execution.

    FEX feedback is evaluated only when the caller explicitly supplies a ledger
    path. The cycle never writes predictions/outcomes or trains a model.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    coherence = pairwise_coherence(signals)
    opposing = counterevidence(requested_decision, signals)
    dsx = cognitive_execution_guard(coherence, opposing, panic=panic)
    dsx_gate = {
        "status": "approved" if dsx["allowed"] else "veto",
        "independent": True,
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
        ),
        build_provenance(
            name="safety_gate",
            module="DSX.cognitive_execution_guard",
            version="existing",
            inputs={"coherence": coherence, "counterevidence": opposing, "panic": panic},
            output=dsx_gate,
            status="blocked" if dsx["blocked"] else "approved",
            vector="DSX",
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
                "predictions_recorded": fex_report["predictions_recorded"],
                "outcomes_scored": fex_report["outcomes_scored"],
                "automatic_retraining": False,
            },
            status=fex_report["report_status"],
            vector="FEX",
        ))
    trace = aggregate_cycle(cycle_id, records)
    result = build_cycle(
        cycle_id=cycle_id,
        observed_at=timestamp,
        source_status="valid",
        context_ref=context_ref,
        signals=signals,
        uncertainty=uncertainty,
        prediction=dict(prediction or {}),
        regulation={"state": "review" if dsx["blocked"] else "normal"},
        decision=requested_decision,
        risk_gate=dsx_gate,
        outcome=outcome,
        mode="PAPER",
    )
    result["diagnostics"] = {
        "coherence": coherence,
        "counterevidence": opposing,
        "dsx": dsx,
        "trace": trace,
        "fex_feedback": fex_report,
    }
    return result
