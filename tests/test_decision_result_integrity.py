from __future__ import annotations

import json

import pytest

from elite.contracts.builder import (
    build_decision_result,
    verify_decision_result_hash,
)
from elite.contracts.result_store import (
    append_result,
    get_result,
    verify_result_store,
)


def _record():
    from types import SimpleNamespace

    state = SimpleNamespace(
        decision="hold",
        percepcion_espacial={"cycle_id": "integrity-test-cycle", "analisis_financiero": {}},
    )
    cognitive = {
        "provenance": [{
            "id": "SCX:integrity:1:aaaaaaaaaaaaaaaa",
            "modulo": "tests.integrity",
            "input_hash": "a" * 64,
            "status": "synthetic",
        }],
        "cathedral_verdict": {
            "status": "BLOCKED_UNCERTAINTY",
            "evaluation_hash": "b" * 64,
            "reason": "synthetic_test",
        },
    }
    return build_decision_result(
        state, cognitive, trace_id="1234567890abcdef1234567890abcdef"
    )


def test_builder_hash_covers_all_decision_result_fields():
    record = _record()
    assert verify_decision_result_hash(record)
    record["risks"] = ["tampered"]
    assert not verify_decision_result_hash(record)


def test_store_appends_and_verifies_hash_chain(tmp_path):
    path = tmp_path / "results.jsonl"
    first = _record()
    second = _record()
    append_result(first, path)
    append_result(second, path)

    report = verify_result_store(path)
    assert report["valid"] is True
    assert report["record_count"] == 2
    assert get_result(first["result_id"], path)["store_integrity"]["sequence"] == 1
    assert get_result(second["result_id"], path)["store_integrity"]["sequence"] == 2


def test_store_detects_modified_contract_field(tmp_path):
    path = tmp_path / "results.jsonl"
    record = _record()
    append_result(record, path)
    stored = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    stored["decision"] = "buy"
    path.write_text(json.dumps(stored) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contract_hash"):
        get_result(record["result_id"], path)


def test_store_detects_deleted_or_reordered_history(tmp_path):
    path = tmp_path / "results.jsonl"
    first, second = _record(), _record()
    append_result(first, path)
    append_result(second, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(lines[1] + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="discontinuo"):
        verify_result_store(path)


def test_store_does_not_silently_skip_malformed_json(tmp_path):
    path = tmp_path / "results.jsonl"
    path.write_text("{malformed}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON inválido"):
        get_result("missing", path)


def test_store_rejects_unmigrated_legacy_history(tmp_path):
    path = tmp_path / "results.jsonl"
    path.write_text(json.dumps({"result_id": "legacy"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="historial legado"):
        append_result(_record(), path)


def test_store_rejects_tampered_record_chain_hash(tmp_path):
    path = tmp_path / "results.jsonl"
    record = _record()
    append_result(record, path)
    stored = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    stored["store_integrity"]["record_hash"] = "0" * 64
    path.write_text(json.dumps(stored) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash de cadena"):
        verify_result_store(path)
