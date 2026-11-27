"""Composition boundary joining SCX diagnostics with FEX memory and MSX provenance.

SCX calculations remain in cognitive_state.py. This module is the explicit
integration layer; it does not enforce decisions or authorize financial execution.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from FEX.FEEDBACK.feedback_loop import resumir_memoria_decisiones
from MSX.provenance import aggregate_cycle, build_provenance

from .cognitive_state import (
    SCHEMA_VERSION,
    counterevidence,
    metacognition,
    pairwise_coherence,
    regime_context,
)


def build_cognitive_report(
    *,
    decision: str,
    signals: Iterable[dict[str, Any]],
    regime_history: Iterable[str] = (),
    decision_history: Iterable[str] = (),
    epistemic_sigma: float | None = None,
    aleatoric_sigma: float | None = None,
    confidence: float | None = None,
    historical_accuracy: float | None = None,
    error_slope: float | None = None,
    input_evidence: Any = None,
) -> dict[str, Any]:
    """Compose diagnostics and close a verifiable provenance manifest when cycle-bound."""
    signals = list(signals)
    coherence = pairwise_coherence(signals)
    counter = counterevidence(decision, signals)
    meta = metacognition(
        coherence=coherence,
        epistemic_sigma=epistemic_sigma,
        aleatoric_sigma=aleatoric_sigma,
        confidence=confidence,
        historical_accuracy=historical_accuracy,
        error_slope=error_slope,
    )
    cycle_id = input_evidence.get("cycle_id") if isinstance(input_evidence, dict) else None
    cognitive_inputs = (
        input_evidence
        if input_evidence is not None
        else {"decision": decision, "signals": signals}
    )
    provenance = build_provenance(
        "cognitive_report",
        "elite.REASON.cognitive_state",
        SCHEMA_VERSION,
        cognitive_inputs,
        output={"coherence_status": coherence["evidence_status"]},
        status="computed_with_gaps",
        vector="SCX",
        parent=cycle_id,
    )

    source_records = {}
    source_inputs_by_id: dict[str, Any] = {}
    for signal in signals:
        source_name = str(signal.get("name", "unknown"))
        source_inputs = {
            "direction": signal.get("direction"),
            "confidence": signal.get("confidence"),
            "confidence_kind": signal.get("confidence_kind"),
        }
        source_record = build_provenance(
            source_name,
            str(signal.get("module", "caller_supplied_signal")),
            str(signal.get("version", "unknown")),
            source_inputs,
            output={
                "direction": signal.get("direction"),
                "confidence_kind": signal.get("confidence_kind"),
            },
            confidence=signal.get("confidence"),
            status="observed_heuristic_not_calibrated",
            vector=(
                "RSX"
                if source_name.lower().startswith(("sensor", "perceiv", "market_data"))
                else "SCX"
            ),
            parent=cycle_id,
        )
        source_records[source_name] = source_record
        source_inputs_by_id[source_record["id"]] = source_inputs

    records = [provenance, *source_records.values()]
    cycle_trace = None
    if cycle_id:
        original_inputs = {
            provenance["id"]: cognitive_inputs,
            **{
                record["id"]: source_inputs_by_id[record["id"]]
                for record in source_records.values()
            },
        }
        cycle_trace = aggregate_cycle(
            str(cycle_id),
            records,
            original_inputs=original_inputs,
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "coherencia": coherence,
        "contraevidencia": counter,
        "metacognicion": meta,
        "contexto": regime_context(regime_history),
        "memoria": resumir_memoria_decisiones(list(decision_history)),
        "provenance": {
            "cognitive_report": provenance,
            "sources": source_records,
            "cycle_trace": cycle_trace,
        },
        "operational_policy": {
            "trading_enabled": False,
            "orders_created": False,
            "orders_executed": False,
            "status": "analysis_only",
        },
    }
