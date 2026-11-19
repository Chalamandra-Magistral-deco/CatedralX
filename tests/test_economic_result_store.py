from __future__ import annotations

import copy
import json

import pytest

from contracts.result_store import append_result, get_result
from REASON.core_contract import evaluate_economic_opportunity


def _economic_result():
    payload = {
        "opportunity_id": "opp-test-001",
        "name": "Oportunidad sintética",
        "category": "digital_product",
        "income_model": "hybrid",
        "currency": "MXN",
        "horizon_months": 6,
        "capital_required": 1000,
        "available_capital": 500,
        "revenue": [
            {"amount": 100, "frequency": "monthly", "evidence_id": "ev-revenue"}
        ],
        "costs": [
            {"amount": 20, "frequency": "monthly", "evidence_id": "ev-cost"}
        ],
        "evidence": [
            {
                "evidence_id": "ev-revenue",
                "source": "synthetic://revenue-input",
                "digest": "a" * 64,
                "observed_at": "2026-11-18T12:00:00-06:00",
            },
            {
                "evidence_id": "ev-cost",
                "source": "synthetic://cost-input",
                "digest": "b" * 64,
                "observed_at": "2026-11-18T12:00:00-06:00",
            },
        ],
        "assumptions": ["Los importes mensuales se mantienen durante el horizonte."],
        "scenarios": [
            {"name": "conservative", "revenue_multiplier": 0.7, "cost_multiplier": 1.2},
            {"name": "base", "revenue_multiplier": 1.0, "cost_multiplier": 1.0},
            {"name": "optimistic", "revenue_multiplier": 1.3, "cost_multiplier": 0.9},
        ],
        "trace_id": "1234567890abcdef1234567890abcdef",
    }
    return evaluate_economic_opportunity(payload)


def test_result_store_appends_and_recovers_economic_opportunity(tmp_path):
    path = tmp_path / "results.jsonl"
    result = _economic_result()

    result_id = append_result(result, path=path)

    assert result_id == result["result_id"]
    stored = get_result(result_id, path=path)
    assert stored == result
    assert stored["status"] == "ANALYSIS_COMPLETE"
    assert stored["authorization"] == "NOT_GRANTED"
    assert stored["analysis_only"] is True
    assert stored["orders_created"] is False
    assert stored["orders_executed"] is False


def test_result_store_rejects_duplicate_result_id(tmp_path):
    path = tmp_path / "results.jsonl"
    result = _economic_result()
    append_result(result, path=path)

    with pytest.raises(ValueError, match="result_id duplicado"):
        append_result(result, path=path)


def test_result_store_rejects_economic_hash_tampering(tmp_path):
    result = copy.deepcopy(_economic_result())
    result["risk_flags"].append("tampered_after_hash")

    with pytest.raises(ValueError, match="evaluation_hash"):
        append_result(result, path=tmp_path / "results.jsonl")


def test_result_store_rejects_economic_execution_flags(tmp_path):
    result = copy.deepcopy(_economic_result())
    result["orders_executed"] = True
    # Recompute the package hash so the execution guard, not the hash guard, is exercised.
    from contracts.result_store import _opportunity_hash
    result["evaluation_hash"] = _opportunity_hash(result)

    with pytest.raises(ValueError, match="límites de no ejecución"):
        append_result(result, path=tmp_path / "results.jsonl")


def test_economic_result_jsonl_is_valid_json_and_retrievable_without_bulk_load(tmp_path):
    path = tmp_path / "results.jsonl"
    result = _economic_result()
    append_result(result, path=path)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["result_id"] == result["result_id"]
