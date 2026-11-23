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
    assert result["next_action"] == "SOLICITAR_ACEPTACION_INDEPENDIENTE"
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


def test_result_store_append_is_0600_and_does_not_change_record_shape(tmp_path):
    # H-04 (partial): flock + fsync + 0600 without changing the stored
    # record format — the verify script compares stored == decision exactly.
    import json
    import os

    path = tmp_path / "nested" / "results.jsonl"
    result = build_decision_result(_make_state(decision="buy"), _make_cognitive())
    append_result(result, path=path)
    assert (os.stat(path).st_mode & 0o777) == 0o600
    assert (os.stat(path.parent).st_mode & 0o777) == 0o700
    stored = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert stored["record"] == result
    assert stored["store_integrity"]["sequence"] == 1


def test_result_store_concurrent_appends_keep_all_lines_valid(tmp_path):
    # H-04 (partial): flock serializes writers; no interleaved lines.
    import json
    import threading

    path = tmp_path / "results.jsonl"
    errors: list[BaseException] = []

    def append_one(index: int) -> None:
        try:
            result = build_decision_result(_make_state(decision="buy"), _make_cognitive())
            result["result_id"] = f"{index:032x}"
            append_result(result, path=path)
        except BaseException as exc:  # noqa: BLE001 - collected by the test
            errors.append(exc)

    threads = [threading.Thread(target=append_one, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 8
    records = [json.loads(line) for line in lines]
    assert len({record["record"]["result_id"] for record in records}) == 8
    for index in range(8):
        assert get_result(f"{index:032x}", path=path) is not None

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


def test_result_store_rejects_accepted_status_with_blocked_central_gate(tmp_path):
    result = build_decision_result(_make_state(), _make_cognitive())
    result["evaluation_gate"] = "REJECTED"
    with pytest.raises(ValueError, match="requiere evaluation_gate ACCEPTED"):
        append_result(result, path=tmp_path / "results.jsonl")


def test_result_store_rejects_accepted_evidence_without_digest(tmp_path):
    result = build_decision_result(_make_state(), _make_cognitive())
    result["evidence"][0]["digest"] = None
    with pytest.raises(ValueError, match="evidencia incompleta"):
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


def _economic_integrity_fixture(result_id="00000000000000000000000000000002"):
    from elite.contracts.result_store import _opportunity_hash

    scenario = {
        "revenue_total": 1200.0, "cost_total": 240.0, "net_result": 960.0,
        "net_margin_pct": 80.0, "roi_pct": 96.0, "payback_months": 1.0,
        "decision_candidate": "PURSUE",
    }
    record = {
        "schema_version": "catedralx.economic-opportunity/1.0",
        "result_id": result_id, "engine": "CatedralX",
        "evaluation_domain": "business_opportunity", "status": "ANALYSIS_COMPLETE",
        "opportunity_id": "synthetic-opportunity", "income_model": "hybrid",
        "currency": "MXN", "horizon_months": 6,
        "financials": {
            "capital_required": 100.0, "available_capital": 100.0, "funding_gap": 0.0,
            "revenue_total_base_input": 1200.0, "cost_total_base_input": 240.0,
            "initial_capital_status": "funded",
            "working_capital_assessment": "not_assessed_without_periodic_cashflow",
            "tax_assessment": "not_included_unless_declared_as_cost_line",
        },
        "scenarios": {"conservative": scenario, "base": scenario, "optimistic": scenario},
        "decision_candidate": "PURSUE", "risk_flags": [],
        "assumptions": ["Synthetic test assumptions."],
        "evidence": [{
            "evidence_id": "ev-1", "source": "synthetic://test", "digest": "c" * 64,
            "observed_at": "2026-11-23T12:00:00-06:00",
        }],
        "evidence_status": "declared_digest_not_source_authentication",
        "uncertainty": {"status": "not_probability_calibrated", "note": "Synthetic."},
        "provenance": {"input_sha256": "d" * 64},
        "trace_id": "1234567890abcdef1234567890abcdef",
        "evaluation_hash": "", "analysis_only": True, "orders_created": False,
        "orders_executed": False, "authorization": "NOT_GRANTED",
        "independent_acceptance_required": True,
    }
    record["evaluation_hash"] = _opportunity_hash(record)
    return record


def test_result_store_integrity_chains_both_contract_types(tmp_path):
    from elite.contracts.result_store import verify_result_store

    path = tmp_path / "results.jsonl"
    decision = build_decision_result(
        _make_state(), _make_cognitive(gate_status="BLOCKED_UNCERTAINTY"),
        trace_id="1234567890abcdef1234567890abcdef",
    )
    decision["result_id"] = "00000000000000000000000000000001"
    economic = _economic_integrity_fixture()
    append_result(decision, path)
    append_result(economic, path)

    assert verify_result_store(path)["record_count"] == 2
    assert get_result(decision["result_id"], path) == decision
    assert get_result(economic["result_id"], path) == economic


def test_result_store_integrity_detects_suffix_truncation(tmp_path):
    from elite.contracts.result_store import verify_result_store

    path = tmp_path / "results.jsonl"
    decision = build_decision_result(_make_state(), _make_cognitive())
    append_result(decision, path)
    append_result(build_decision_result(_make_state(), _make_cognitive()), path)
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(lines[0] + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Checkpoint"):
        verify_result_store(path)


def test_result_store_integrity_rejects_legacy_without_migration(tmp_path):
    path = tmp_path / "results.jsonl"
    path.write_text('{"result_id":"legacy"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="legado/no migrado"):
        append_result(build_decision_result(_make_state(), _make_cognitive()), path)


def test_result_store_integrity_rejects_duplicate_id_across_types(tmp_path):
    path = tmp_path / "results.jsonl"
    shared_id = "00000000000000000000000000000004"
    decision = build_decision_result(_make_state(), _make_cognitive())
    decision["result_id"] = shared_id
    append_result(decision, path)
    with pytest.raises(ValueError, match="duplicado"):
        append_result(_economic_integrity_fixture(shared_id), path)


def test_result_store_integrity_detects_record_tampering(tmp_path):
    import json
    from elite.contracts.result_store import verify_result_store

    path = tmp_path / "results.jsonl"
    result = build_decision_result(_make_state(), _make_cognitive())
    append_result(result, path)
    envelope = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    envelope["record"]["decision"] = "sell"
    path.write_text(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contenido alterado|Hash de cadena"):
        verify_result_store(path)


def test_result_store_integrity_detects_checkpoint_rewrite(tmp_path):
    import json
    from elite.contracts.result_store import verify_result_store

    path = tmp_path / "results.jsonl"
    append_result(build_decision_result(_make_state(), _make_cognitive()), path)
    checkpoint = path.with_name(path.name + ".head")
    value = json.loads(checkpoint.read_text(encoding="utf-8"))
    value["head_hash"] = "f" * 64
    checkpoint.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Checkpoint no coincide"):
        verify_result_store(path)
