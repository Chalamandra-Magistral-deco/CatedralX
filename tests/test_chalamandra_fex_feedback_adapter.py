"""FEX adapter tests use temporary paths and never touch default user state."""
from datetime import datetime, timedelta, timezone

import pytest

from REASON.fex_feedback_adapter import (
    evaluate_ledger,
    record_observed_outcome,
    record_prediction,
    summarize_observed_decisions,
)


def test_adapter_requires_explicit_ledger_path():
    with pytest.raises(ValueError, match="ruta explícita"):
        record_prediction(path=None, prediction={"decision": "buy"})


def test_prediction_is_pending_until_an_observed_outcome(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    prediction_id = record_prediction(
        path=ledger,
        prediction={
            "decision": "buy",
            "reference_price": 100.0,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "market_source": "synthetic-test",
        },
    )
    report = evaluate_ledger(path=ledger)
    assert prediction_id
    assert report["predictions_recorded"] == 1
    assert report["predictions_pending_outcome"] == 1
    assert report["outcomes_scored"] == 0
    assert report["automatic_retraining"] is False
    assert report["orders_executed"] is False


def test_observed_outcome_is_scored_only_after_horizon(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    start = datetime.now(timezone.utc) - timedelta(seconds=65)
    prediction_id = record_prediction(
        path=ledger,
        prediction={
            "decision": "buy",
            "reference_price": 100.0,
            "observed_at": start.isoformat(),
            "market_source": "synthetic-test",
        },
    )
    record_observed_outcome(
        path=ledger,
        prediction_id=prediction_id,
        outcome={
            "horizon": "1m",
            "observed_price": 101.0,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "source": "synthetic-test",
        },
    )
    report = evaluate_ledger(path=ledger)
    assert report["outcomes_scored"] == 1
    assert report["metrics_by_horizon"]["1m"]["labelled_count"] == 1
    assert report["automatic_retraining"] is False


def test_observed_decision_summary_does_not_claim_performance():
    result = summarize_observed_decisions(["buy", "hold", "sell", "unknown"])
    assert result["ciclos_observados"] == 3
    assert result["evidence_status"] == "computed_from_observed_decisions"
    assert "pnl" not in result
    assert "accuracy" not in result


def test_outcome_rejects_mismatched_market_source_without_appending(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    prediction_id = record_prediction(
        path=ledger,
        prediction={
            "decision": "buy",
            "reference_price": 100.0,
            "observed_at": (datetime.now(timezone.utc) - timedelta(seconds=65)).isoformat(),
            "market_source": "source-a",
        },
    )
    before = ledger.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="no coincide"):
        record_observed_outcome(
            path=ledger,
            prediction_id=prediction_id,
            outcome={
                "horizon": "1m",
                "observed_price": 101.0,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "source": "source-b",
            },
        )
    assert ledger.read_text(encoding="utf-8") == before


def test_outcome_rejects_unelapsed_horizon_without_appending(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    prediction_id = record_prediction(
        path=ledger,
        prediction={
            "decision": "buy",
            "reference_price": 100.0,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "market_source": "synthetic-test",
        },
    )
    before = ledger.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="Horizonte aún no vencido"):
        record_observed_outcome(
            path=ledger,
            prediction_id=prediction_id,
            outcome={
                "horizon": "1m",
                "observed_price": 101.0,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "source": "synthetic-test",
            },
        )
    assert ledger.read_text(encoding="utf-8") == before


def test_corrupt_ledger_is_rejected_without_modifying_file(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    original = '{not-valid-json}\n'
    ledger.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="JSONL inválido"):
        evaluate_ledger(path=ledger)
    assert ledger.read_text(encoding="utf-8") == original
