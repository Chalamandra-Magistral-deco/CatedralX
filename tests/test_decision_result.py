from types import SimpleNamespace

import pytest

from elite.contracts.builder import build_decision_result
from elite.contracts.result_store import append_result, get_result


def _make_state(decision="buy", risk_flags=None):
    return SimpleNamespace(
        decision=decision,
        percepcion_espacial={
            "cycle_id": "test-cycle-123",
            "analisis_financiero": {"risk_flags": risk_flags or []}
        }
    )

def _make_cognitive(disonancia=0.0, contraevidencia=0.0, prov_records=None, gate_status="ACCEPTED"):
    return {
        "coherencia": {"disonancia": disonancia},
        "contraevidencia": {"fuerza_contra": contraevidencia},
        "provenance": prov_records or [],
        "cathedral_verdict": {"status": gate_status, "evaluation_hash": "a" * 64},
    }

def test_build_decision_result_accepted():
    state = _make_state(decision="buy")
    cognitive = _make_cognitive(disonancia=0.1, contraevidencia=0.1)
    result = build_decision_result(state, cognitive, trace_id="1234567890abcdef1234567890abcdef")

    assert result["status"] == "ACCEPTED"
    assert result["decision"] == "buy"
    assert result["engine"] == "CatedralX"
    assert result["evaluation_hash"] == "a" * 64
    assert result["evaluation_gate"] == "ACCEPTED"
    assert result["trace_id"] == "1234567890abcdef1234567890abcdef"
    assert result["analysis_only"] is True
    assert result["orders_created"] is False
    assert result["orders_executed"] is False
    assert "result_id" in result

def test_build_decision_result_uncertain():
    state = _make_state(decision="hold")
    cognitive = _make_cognitive(disonancia=0.5, contraevidencia=0.1)
    result = build_decision_result(state, cognitive)

    assert result["status"] == "UNCERTAIN"
    assert result["next_action"] == "Manual review required"

def test_build_decision_result_rejected():
    state = _make_state(decision="sell")
    cognitive = _make_cognitive(disonancia=0.9, contraevidencia=0.1)
    result = build_decision_result(state, cognitive)

    assert result["status"] == "REJECTED"
    assert result["next_action"] == "Manual review required"

def test_result_store_append_and_get(tmp_path):
    path = tmp_path / "results.jsonl"
    state = _make_state(decision="buy")
    cognitive = _make_cognitive()
    result = build_decision_result(state, cognitive)

    result_id = append_result(result, path=path)
    assert result_id == result["result_id"]
    assert path.exists()

    retrieved = get_result(result_id, path=path)
    assert retrieved is not None
    assert retrieved["result_id"] == result_id
    assert retrieved["status"] == result["status"]

def test_result_store_not_found(tmp_path):
    path = tmp_path / "empty.jsonl"
    assert get_result("non-existent", path=path) is None


def test_build_decision_result_fails_closed_without_central_hash():
    state = _make_state(decision="buy")
    cognitive = _make_cognitive()
    cognitive["cathedral_verdict"].pop("evaluation_hash")
    with pytest.raises(ValueError, match="evaluation_hash SHA-256"):
        build_decision_result(state, cognitive)


@pytest.mark.parametrize("gate_status", ["BLOCKED_UNCERTAINTY", "BLOCKED_DEFICIT"])
def test_new_blocked_gate_statuses_map_to_uncertain(gate_status):
    result = build_decision_result(
        _make_state(decision="buy"),
        _make_cognitive(disonancia=0.1, contraevidencia=0.1, gate_status=gate_status),
    )
    assert result["evaluation_gate"] == gate_status
    assert result["status"] == "UNCERTAIN"
    assert result["next_action"] == "Manual review required"


def test_missing_central_inputs_have_explicit_block_code_and_preserve_reasons(tmp_path):
    cognitive = _make_cognitive(gate_status="BLOCKED_UNCERTAINTY")
    cognitive["cathedral_verdict"].update({
        "reason": "ENTRADAS_CUANTITATIVAS_INVALIDAS_O_FALTANTES",
        "invalid_inputs": ["evidence", "human_value", "reinvestment"],
        "blocking_reasons": ["DYNAMIC_GOVERNANCE_NOT_VERIFIED"],
    })
    result = build_decision_result(_make_state(), cognitive)

    assert result["status"] == "BLOCKED_MISSING_INPUT"
    assert result["evaluation_gate"] == "BLOCKED_UNCERTAINTY"
    assert result["missing_inputs"] == ["evidence", "human_value", "reinvestment"]
    assert result["blocking_reasons"] == ["DYNAMIC_GOVERNANCE_NOT_VERIFIED"]
    assert result["evaluation_reason"] == "ENTRADAS_CUANTITATIVAS_INVALIDAS_O_FALTANTES"
    result_id = append_result(result, path=tmp_path / "results.jsonl")
    assert get_result(result_id, path=tmp_path / "results.jsonl")["status"] == "BLOCKED_MISSING_INPUT"


@pytest.mark.parametrize(
    "gate_status",
    ["BLOCKED_EVIDENCE", "BLOCKED_REINVERSION", "BLOCKED_UNCERTAINTY", "BLOCKED_DEFICIT"],
)
def test_high_cognitive_dissonance_cannot_override_a_blocked_gate(gate_status):
    cognitive = _make_cognitive(disonancia=0.99, contraevidencia=0.99, gate_status=gate_status)
    result = build_decision_result(_make_state(decision="buy"), cognitive)
    assert result["evaluation_gate"] == gate_status
    assert result["status"] == "UNCERTAIN"
