"""Synthetic integration tests through existing SCX, DSX and MSX vectors."""
from REASON.master_cycle import run_synthetic_master_cycle


def test_master_cycle_integrates_vectors_and_emits_non_executable_intent():
    result = run_synthetic_master_cycle(
        cycle_id="integration-001",
        signals=[
            {"name": "trend", "direction": "buy", "confidence": 0.9},
            {"name": "momentum", "direction": "buy", "confidence": 0.8},
        ],
        requested_decision="BUY",
        prediction={"value": 100.0},
    )
    assert result["schema_version"] == "chalamandra-core/1.0"
    assert result["diagnostics"]["dsx"]["allowed"] is True
    assert result["diagnostics"]["trace"]["record_count"] == 2
    assert result["decision"]["final"] == "BUY"
    assert result["action"]["executable"] is False
    assert result["prediction_error"]["value"] is None


def test_master_cycle_dsx_veto_on_panic():
    result = run_synthetic_master_cycle(
        cycle_id="integration-panic",
        signals=[{"name": "trend", "direction": "buy", "confidence": 0.8}],
        requested_decision="BUY",
        panic=True,
    )
    assert result["diagnostics"]["dsx"]["blocked"] is True
    assert "panic_active" in result["diagnostics"]["dsx"]["reasons"]
    assert result["decision"]["final"] == "HOLD"
    assert result["action"]["status"] == "blocked"
    assert result["action"]["executable"] is False


def test_master_cycle_vetoes_measured_conflicting_signals():
    result = run_synthetic_master_cycle(
        cycle_id="integration-conflict",
        signals=[
            {"name": "trend", "direction": "buy", "confidence": 0.95},
            {"name": "momentum", "direction": "sell", "confidence": 0.95},
        ],
        requested_decision="BUY",
    )
    assert result["diagnostics"]["dsx"]["blocked"] is True
    assert result["decision"]["final"] == "HOLD"


def test_master_cycle_prediction_error_requires_observed_outcome():
    result = run_synthetic_master_cycle(
        cycle_id="integration-outcome",
        signals=[{"name": "trend", "direction": "buy", "confidence": 0.8}],
        requested_decision="BUY",
        prediction={"value": 100.0},
        outcome={"value": 101.25},
    )
    assert result["prediction_error"]["value"] == 1.25
    assert result["prediction_error"]["status"] == "computed_from_observed_outcome"


def test_master_cycle_reads_explicit_fex_ledger_without_writing(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    ledger.write_text("", encoding="utf-8")
    result = run_synthetic_master_cycle(
        cycle_id="integration-fex",
        signals=[{"name": "trend", "direction": "buy", "confidence": 0.8}],
        requested_decision="BUY",
        fex_feedback_path=ledger,
    )
    assert result["diagnostics"]["fex_feedback"]["predictions_recorded"] == 0
    assert result["diagnostics"]["fex_feedback"]["automatic_retraining"] is False
    assert result["diagnostics"]["trace"]["record_count"] == 3
    assert ledger.read_text(encoding="utf-8") == ""
    assert result["action"]["executable"] is False


def test_master_cycle_dsx_veto_remains_authoritative_with_fex_enabled(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    ledger.write_text("", encoding="utf-8")
    result = run_synthetic_master_cycle(
        cycle_id="integration-fex-panic",
        signals=[{"name": "trend", "direction": "buy", "confidence": 0.8}],
        requested_decision="BUY",
        panic=True,
        fex_feedback_path=ledger,
    )
    assert result["diagnostics"]["dsx"]["blocked"] is True
    assert result["decision"]["final"] == "HOLD"
    assert result["action"]["status"] == "blocked"
    assert result["action"]["executable"] is False
    assert result["diagnostics"]["trace"]["record_count"] == 3
    assert ledger.read_text(encoding="utf-8") == ""
