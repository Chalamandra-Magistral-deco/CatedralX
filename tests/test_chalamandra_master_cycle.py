"""Governance and provenance regression tests for the synthetic master cycle."""
from __future__ import annotations

import json

import pytest

from REASON import master_cycle


OBSERVED_AT = "2026-11-19T12:00:00+00:00"
SIGNALS = [
    {"name": "trend_a", "direction": "buy", "confidence": 0.8},
    {"name": "trend_b", "direction": "buy", "confidence": 0.9},
]


def test_cognitive_approval_never_claims_independent_acceptance():
    result = master_cycle.run_synthetic_master_cycle(
        cycle_id="cycle-governance-1",
        signals=SIGNALS,
        requested_decision="BUY",
        observed_at=OBSERVED_AT,
    )

    gate = result["risk_gate"]
    assert gate["status"] == "approved"
    assert gate["cognitive_gate_status"] == "approved"
    assert gate["independent"] is False
    assert gate["acceptance_status"] == "not_provided"
    assert result["diagnostics"]["independent_acceptance"] == {
        "status": "not_provided",
        "verified": False,
        "required_for_non_hold_decision": True,
    }
    assert result["decision"]["final"] == "HOLD"
    assert result["action"]["status"] == "blocked"
    assert result["action"]["executable"] is False


def test_source_status_remains_unknown_without_source_authentication():
    result = master_cycle.run_synthetic_master_cycle(
        cycle_id="cycle-source-1",
        signals=SIGNALS,
        requested_decision="BUY",
        observed_at=OBSERVED_AT,
    )
    assert result["source_status"] == "unknown"
    assert result["decision"]["final"] == "HOLD"


def test_explicit_observed_at_makes_core_and_msx_trace_reproducible():
    first = master_cycle.run_synthetic_master_cycle(
        cycle_id="cycle-repeatable",
        signals=SIGNALS,
        requested_decision="BUY",
        observed_at=OBSERVED_AT,
    )
    second = master_cycle.run_synthetic_master_cycle(
        cycle_id="cycle-repeatable",
        signals=SIGNALS,
        requested_decision="BUY",
        observed_at=OBSERVED_AT,
    )

    assert first["observed_at"] == second["observed_at"]
    assert first["provenance"]["record_sha256"] == second["provenance"]["record_sha256"]
    assert first["diagnostics"]["trace"] == second["diagnostics"]["trace"]
    assert first["diagnostics"]["trace"]["record_count"] == 4
    assert any(
        item["module"] == "REASON.core_contract.build_cycle"
        for item in first["diagnostics"]["trace"]["records"]
    )


@pytest.mark.parametrize(
    "observed_at",
    ["", "not-a-date", "2026-11-19T12:00:00", "2026-99-99T12:00:00Z"],
)
def test_invalid_or_naive_observed_at_is_rejected(observed_at):
    with pytest.raises(ValueError):
        master_cycle.run_synthetic_master_cycle(
            cycle_id="cycle-invalid-time",
            signals=SIGNALS,
            observed_at=observed_at,
        )


@pytest.mark.parametrize(
    "signals",
    [
        None,
        "not-a-list",
        [{"name": "valid"}, "not-an-object"],
    ],
)
def test_invalid_signal_container_is_rejected(signals):
    with pytest.raises(ValueError):
        master_cycle.run_synthetic_master_cycle(
            cycle_id="cycle-invalid-signals",
            signals=signals,
            observed_at=OBSERVED_AT,
        )


def test_fex_evaluation_requires_explicit_path_and_is_read_only(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    ledger.write_text("", encoding="utf-8")
    before = ledger.read_bytes()

    result = master_cycle.run_synthetic_master_cycle(
        cycle_id="cycle-fex-readonly",
        signals=SIGNALS,
        observed_at=OBSERVED_AT,
        fex_feedback_path=ledger,
    )

    assert result["diagnostics"]["fex_feedback"]["report_status"] == "ok"
    assert result["diagnostics"]["fex_feedback"]["automatic_retraining"] is False
    assert result["diagnostics"]["fex_feedback"]["orders_executed"] is False
    assert ledger.read_bytes() == before


def test_fex_is_absent_when_no_explicit_path_is_supplied():
    result = master_cycle.run_synthetic_master_cycle(
        cycle_id="cycle-no-fex",
        signals=SIGNALS,
        observed_at=OBSERVED_AT,
    )
    assert result["diagnostics"]["fex_feedback"] is None
    assert all(
        item["vector"] != "FEX"
        for item in result["diagnostics"]["trace"]["records"]
    )
