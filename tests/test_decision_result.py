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
        "provenance": (
            [{
                "id": "SCX:fixture:1:aaaaaaaaaaaaaaaa",
                "modulo": "tests.synthetic_fixture",
                "input_hash": "a" * 64,
                "timestamp": 1735689600,
                "status": "synthetic_test_evidence",
            }]
            if prov_records is None else prov_records
        ),
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

def test_build_decision_result_extracts_canonical_msx_cycle_trace():
    cognitive_record = {
        "id": "SCX:cognitive:1735689600:aaaaaaaaaaaaaaaa",
        "vector": "SCX",
        "modulo": "elite.REASON.cognitive_state",
        "version": "1.0",
        "timestamp": 1735689600,
        "input_hash": "a" * 64,
        "status": "computed",
    }
    source_record = {
        "id": "RSX:market:1735689601:bbbbbbbbbbbbbbbb",
        "vector": "RSX",
        "modulo": "elite.PERCEIVE.market_data",
        "version": "2.0",
        "timestamp": 1735689601,
        "input_hash": "b" * 64,
        "status": "observed_heuristic_not_calibrated",
    }
    cognitive = _make_cognitive(prov_records={
        "cognitive_report": cognitive_record,
        "sources": {"market_data": source_record},
        "cycle_trace": {
            "cycle_id": "test-cycle-123",
            "records": [cognitive_record, source_record],
            "record_count": 2,
            "status": "aggregated",
        },
    })

    result = build_decision_result(
        _make_state(),
        cognitive,
        trace_id="1234567890abcdef1234567890abcdef",
    )

    assert result["provenance"] == [cognitive_record["id"], source_record["id"]]
    assert len(result["evidence"]) == 2
    assert result["evidence"][0]["source"] == "elite.REASON.cognitive_state"
    assert result["evidence"][0]["vector"] == "SCX"
    assert result["evidence"][0]["version"] == "1.0"
    assert result["evidence"][0]["digest"] == "a" * 64
    assert result["evidence"][0]["observed_at"] == "2025-01-01T00:00:00+00:00"
    assert result["evidence"][1]["source"] == "elite.PERCEIVE.market_data"
    assert result["evidence"][1]["digest"] == "b" * 64


def test_build_decision_result_preserves_legacy_provenance_list():
    record = {
        "id": "SCX:legacy:1:cccccccccccccccc",
        "module": "legacy.module",
        "hash": "c" * 64,
        "status": "computed",
    }
    result = build_decision_result(
        _make_state(),
        _make_cognitive(prov_records=[record]),
        trace_id="1234567890abcdef1234567890abcdef",
    )

    assert result["provenance"] == [record["id"]]
    assert result["evidence"][0]["source"] == "legacy.module"
    assert result["evidence"][0]["digest"] == "c" * 64


def test_build_decision_result_downgrades_acceptance_without_provenance():
    result = build_decision_result(
        _make_state(),
        _make_cognitive(prov_records=[]),
    )
    assert result["status"] == "UNCERTAIN"
    assert result["evidence"] == []
    assert result["provenance"] == []


@pytest.mark.parametrize("bad_trace", ["not-a-trace", "0" * 32, "A" * 32])
def test_invalid_explicit_trace_is_rejected_not_replaced(bad_trace):
    with pytest.raises(ValueError, match="trace_id explícito inválido"):
        build_decision_result(
            _make_state(),
            _make_cognitive(),
            trace_id=bad_trace,
        )


@pytest.mark.parametrize(
    ("raw_decision", "expected"),
    [("COMPRAR", "buy"), ("VENTA", "sell"), ("WAIT", "hold")],
)
def test_decision_builder_reuses_shared_signal_vocabulary(raw_decision, expected):
    result = build_decision_result(
        _make_state(decision=raw_decision),
        _make_cognitive(),
    )
    assert result["decision"] == expected


@pytest.mark.parametrize("bad_decision", ["EXECUTE", "", None])
def test_invalid_decision_is_rejected(bad_decision):
    with pytest.raises(ValueError, match="decisión canónica"):
        build_decision_result(
            _make_state(decision=bad_decision),
            _make_cognitive(),
        )


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

def test_result_store_rejects_accepted_result_without_evidence(tmp_path):
    result = build_decision_result(
        _make_state(),
        _make_cognitive(prov_records=[]),
    )
    result.update({
        "status": "ACCEPTED",
        "evidence": [],
        "provenance": [],
    })
    with pytest.raises(ValueError, match="requiere evidencia y procedencia"):
        append_result(result, path=tmp_path / "results.jsonl")


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
