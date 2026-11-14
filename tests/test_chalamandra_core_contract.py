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
    {"observed_at": "2026-11-11T09:00:00"},
    {"source_status": "maybe"},
    {"decision": "EXECUTE"},
    {"decision": ""},
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


def _opportunity_payload():
    import hashlib
    digest = hashlib.sha256(b"fixture-evidence").hexdigest()
    return {
        "opportunity_id": "opp-001",
        "name": "Servicio digital piloto",
        "category": "digital_service",
        "income_model": "hybrid",
        "currency": "MXN",
        "horizon_months": 12,
        "capital_required": 5000,
        "available_capital": 3000,
        "revenue": [{"amount": 2000, "frequency": "monthly", "evidence_id": "ev-1"}],
        "costs": [{"amount": 500, "frequency": "monthly", "evidence_id": "ev-1"}],
        "evidence": [{
            "evidence_id": "ev-1", "source": "user_supplied_estimate",
            "observed_at": datetime.now(UTC).isoformat(), "digest": digest,
        }],
        "assumptions": ["La facturación mensual estimada se mantiene durante el horizonte."],
        "scenarios": [
            {"name": "conservative", "revenue_multiplier": 0.7, "cost_multiplier": 1.2},
            {"name": "base", "revenue_multiplier": 1.0, "cost_multiplier": 1.0},
            {"name": "optimistic", "revenue_multiplier": 1.2, "cost_multiplier": 0.9},
        ],
        "trace_id": "1234567890abcdef1234567890abcdef",
    }


def test_economic_opportunity_contract_calculates_financial_scenarios_without_authorizing():
    from REASON.core_contract import evaluate_economic_opportunity
    result = evaluate_economic_opportunity(_opportunity_payload())
    assert result["evaluation_domain"] == "business_opportunity"
    assert result["status"] == "ANALYSIS_COMPLETE"
    assert result["scenarios"]["base"]["revenue_total"] == 24000.0
    assert result["scenarios"]["base"]["cost_total"] == 6000.0
    assert result["financials"]["funding_gap"] == 2000.0
    assert result["decision_candidate"] == "DEFER"
    assert result["authorization"] == "NOT_GRANTED"
    assert result["independent_acceptance_required"] is True
    assert result["analysis_only"] is True
    assert result["orders_created"] is False
    assert result["orders_executed"] is False
    assert len(result["evaluation_hash"]) == 64


def test_economic_opportunity_rejects_missing_scenarios_and_unlinked_evidence():
    from REASON.core_contract import evaluate_economic_opportunity
    payload = _opportunity_payload()
    payload["scenarios"] = payload["scenarios"][:2]
    with pytest.raises(ValueError, match="exactamente"):
        evaluate_economic_opportunity(payload)
    payload = _opportunity_payload()
    payload["revenue"][0]["evidence_id"] = "unknown"
    with pytest.raises(ValueError, match="evidence_id"):
        evaluate_economic_opportunity(payload)


def test_economic_opportunity_rejects_boolean_amount_and_noncanonical_trace():
    from REASON.core_contract import evaluate_economic_opportunity
    payload = _opportunity_payload()
    payload["capital_required"] = True
    with pytest.raises(ValueError, match="capital_required"):
        evaluate_economic_opportunity(payload)
    payload = _opportunity_payload()
    payload["trace_id"] = "0" * 32
    with pytest.raises(ValueError, match="trace_id"):
        evaluate_economic_opportunity(payload)


def test_economic_opportunity_cli_dispatches_to_canonical_contract(tmp_path):
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    payload_path = tmp_path / "opportunity.json"
    payload_path.write_text(json.dumps(_opportunity_payload()), encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["CATEDRALX_PYTHON"] = sys.executable
    completed = subprocess.run(
        ["bash", str(root / "BIN/catedral"), "economic-opportunity", "--input-file", str(payload_path)],
        cwd=root, env=env, capture_output=True, text=True, timeout=15, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["engine"] == "CatedralX"
    assert result["evaluation_domain"] == "business_opportunity"
    assert result["trace_id"] == _opportunity_payload()["trace_id"]
