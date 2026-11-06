"""Tests for the additive Chalamandra Core master-cycle contract."""
from datetime import UTC, datetime

import pytest
from REASON.core_contract import build_cycle


def _cycle(**overrides):
    data = {
        "cycle_id": "synthetic-001",
        "observed_at": datetime.now(UTC).isoformat(),
        "source_status": "valid",
        "context_ref": "fixture:market-sample-01",
        "signals": [{"name": "trend", "direction": "up", "confidence": 0.7}],
        "uncertainty": 0.2,
        "prediction": {"value": 101.5, "horizon": "1-step"},
        "regulation": {"attention": "normal"},
        "decision": "BUY",
        "risk_gate": {"status": "approved", "independent": True, "policy_ref": "test-policy"},
        "mode": "PAPER",
    }
    data.update(overrides)
    return build_cycle(**data)


def test_cycle_emits_canonical_contract_and_provenance():
    result = _cycle()
    required = {
        "schema_version", "cycle_id", "observed_at", "source_status",
        "context_ref", "signals", "uncertainty", "prediction",
        "prediction_error", "regulation", "decision", "risk_gate",
        "action", "outcome", "provenance", "mode",
    }
    assert required <= result.keys()
    assert result["decision"]["final"] == "BUY"
    assert result["action"]["status"] == "intent_only"
    assert result["action"]["executable"] is False
    assert len(result["provenance"]["input_sha256"]) == 64
    assert len(result["provenance"]["record_sha256"]) == 64


def test_dsx_veto_fails_closed_to_hold():
    result = _cycle(risk_gate={"status": "veto", "independent": True})
    assert result["decision"]["final"] == "HOLD"
    assert result["action"]["status"] == "blocked"
    assert result["action"]["executable"] is False
    assert result["action"]["reason"] == "risk_gate_not_approved"


def test_missing_or_non_independent_gate_fails_closed():
    assert _cycle(risk_gate={})["decision"]["final"] == "HOLD"
    assert _cycle(risk_gate={"status": "approved", "independent": False})["decision"]["final"] == "HOLD"


def test_invalid_data_and_live_mode_cannot_produce_action_intent():
    invalid = _cycle(source_status="invalid")
    live = _cycle(mode="LIVE")
    assert invalid["decision"]["final"] == "HOLD"
    assert invalid["action"]["status"] == "blocked"
    assert live["decision"]["final"] == "HOLD"
    assert live["action"]["reason"] == "live_disabled"
    assert live["action"]["executable"] is False


def test_prediction_error_waits_for_observed_outcome():
    result = _cycle()
    assert result["prediction_error"] == {
        "value": None, "status": "awaiting_observed_outcome"
    }


def test_prediction_error_is_only_computed_from_observed_numeric_outcome():
    result = _cycle(outcome={"value": 102.0, "observed_at": "fixture-time"})
    assert result["prediction_error"]["value"] == 0.5
    assert result["prediction_error"]["status"] == "computed_from_observed_outcome"


@pytest.mark.parametrize("overrides", [
    {"cycle_id": ""},
    {"observed_at": "not-a-date"},
    {"source_status": "maybe"},
    {"mode": "MAGIC"},
    {"uncertainty": -0.1},
    {"uncertainty": float("nan")},
])
def test_invalid_contract_inputs_are_rejected(overrides):
    with pytest.raises(ValueError):
        _cycle(**overrides)


def test_degraded_or_unknown_source_fails_closed():
    for status in ("degraded", "unknown", "invalid"):
        result = _cycle(source_status=status)
        assert result["decision"]["final"] == "HOLD"
        assert result["action"]["status"] == "blocked"
        assert result["action"]["executable"] is False


def test_live_mode_stays_blocked_even_with_approved_independent_gate():
    result = _cycle(mode="LIVE", risk_gate={"status": "approved", "independent": True})
    assert result["decision"]["final"] == "HOLD"
    assert result["action"]["reason"] == "live_disabled"
    assert result["action"]["executable"] is False


def test_boolean_prediction_value_does_not_create_prediction_error():
    result = _cycle(prediction={"value": True}, outcome={"value": 102.0})
    assert result["prediction_error"]["value"] is None
    assert result["prediction_error"]["status"] == "awaiting_observed_outcome"


def test_non_boolean_or_unapproved_gate_fails_closed():
    for gate in (
        {"status": "approved", "independent": False},
        {"status": "approved", "independent": "true"},
        {"status": "pending", "independent": True},
        None,
    ):
        result = _cycle(risk_gate=gate)
        assert result["decision"]["final"] == "HOLD"
        assert result["action"]["executable"] is False
