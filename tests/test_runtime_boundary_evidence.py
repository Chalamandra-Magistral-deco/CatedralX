"""Isolated runtime probes for cross-domain correlation and durable writes.

These probes use temporary JSONL files and a mocked Agents transport. They do
not contact production services, authorize real operations, or place orders.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
ELITE = ROOT / "elite"
BIN = ELITE / "bin"
for entry in (str(ELITE), str(BIN)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from FEX.FEEDBACK.feedback_loop import registrar_prediccion  # noqa: E402
from FEX.GOVERNANCE.economic_cycle import registrar_evento  # noqa: E402
from contracts.result_store import append_result, get_result  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "dispatch_authorized_cycles_probe", BIN / "dispatch_authorized_cycles.py"
)
assert SPEC and SPEC.loader
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


def _authorized_cycle(path: Path, trace_id: str | None = None) -> str:
    now = datetime.now(UTC).isoformat()
    cycle_id = registrar_evento(
        "measure",
        {"metric": "probe_metric", "source": "synthetic_probe", "period": "test",
         "unit": "count", "formula": "count", "value": 1, "observed_at": now},
        path=path, trace_id=trace_id,
    )
    registrar_evento(
        "evaluate", {"assessment": "synthetic", "evidence": "probe only"},
        path=path, cycle_id=cycle_id, trace_id=trace_id,
    )
    registrar_evento(
        "propose", {"proposal": "review only", "expected_outcome": "candidate",
                    "verification_plan": "independent review"},
        path=path, cycle_id=cycle_id, trace_id=trace_id,
    )
    registrar_evento(
        "authorize",
        {"approved": True, "approver": "probe-owner", "rationale": "isolated test",
         "identity_assertion": {"signed": "probe-only"}},
        path=path, cycle_id=cycle_id, trace_id=trace_id,
    )
    return cycle_id


def test_feedback_prediction_write_persists_upstream_trace_id(tmp_path):
    ledger = tmp_path / "feedback.jsonl"
    trace_id = "a" * 32
    cycle_id = "feedback-cycle-probe"
    # This mirrors REASON.razon.main: trace_id is present before prediction persistence.
    prediction = {
        "cycle_id": cycle_id,
        "trace_id": trace_id,
        "decision": "hold",
        "reference_price": 100.0,
        "observed_at": datetime.now(UTC).isoformat(),
        "market_source": "synthetic_probe",
        "trading_enabled": False,
        "orders_created": False,
        "orders_executed": False,
    }
    prediction_id = registrar_prediccion(prediction, ledger)
    persisted = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])

    assert persisted["prediction_id"] == prediction_id
    assert persisted["prediction"]["cycle_id"] == cycle_id
    assert persisted["prediction"]["trace_id"] == trace_id


def test_economic_ledger_write_is_real_and_keeps_governance_separate_from_trace(tmp_path):
    ledger = tmp_path / "impact_cycle.jsonl"
    trace_id = "e" * 32
    cycle_id = registrar_evento(
        "measure",
        {"metric": "qualified_leads", "source": "synthetic_probe", "period": "test",
         "unit": "count", "formula": "count", "value": 2,
         "observed_at": datetime.now(UTC).isoformat()},
        path=ledger, trace_id=trace_id,
    )
    registrar_evento(
        "evaluate", {"assessment": "measured", "evidence": "synthetic only"},
        path=ledger, cycle_id=cycle_id, trace_id=trace_id,
    )
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]

    assert [row["event_type"] for row in rows] == ["measure", "evaluate"]
    assert {row["cycle_id"] for row in rows} == {cycle_id}
    assert {row["trace_id"] for row in rows} == {trace_id}
    assert all(row["controls"]["money_moved"] is False for row in rows)



def test_economic_ledger_rejects_trace_id_changes_within_cycle(tmp_path):
    ledger = tmp_path / "impact_cycle.jsonl"
    cycle_id = registrar_evento(
        "measure",
        {"metric": "m", "source": "synthetic_probe", "period": "test",
         "unit": "count", "formula": "count", "value": 1,
         "observed_at": datetime.now(UTC).isoformat()},
        path=ledger, trace_id="f" * 32,
    )
    import pytest

    with pytest.raises(ValueError, match="no coincide"):
        registrar_evento(
            "evaluate", {"assessment": "test", "evidence": "synthetic"},
            path=ledger, cycle_id=cycle_id, trace_id="1" * 32,
        )

def test_authorized_dispatch_propagates_upstream_traceparent(monkeypatch, tmp_path):
    from AEX.DECISION import ordenes

    monkeypatch.setattr(
        ordenes,
        "APPROVER_IDENTITY_VERIFIER",
        lambda assertion, decision, price: {
            "verified": assertion == {"signed": "probe-only"},
            "subject": "probe-owner",
            "permissions": ["economic_cycle_authorize"],
        },
    )
    ledger = tmp_path / "impact_cycle.jsonl"
    dispatch_log = tmp_path / "dispatches.jsonl"
    trace_id = "a" * 32
    cycle_id = _authorized_cycle(ledger, trace_id=trace_id)
    observed = {}

    def fake_dispatch(objective, payload, api_url, secret, timeout=5.0,
                      idempotency_key=None, traceparent=None):
        observed.update(objective=objective, cycle_id=payload["cycle_id"],
                        idempotency_key=idempotency_key, traceparent=traceparent)
        return {"status": "queued", "run_id": "probe-run", "task_id": "probe-task",
                "trace_id": trace_id}

    monkeypatch.setattr(scanner, "dispatch_task", fake_dispatch)
    result = scanner.scan_and_dispatch(
        ledger=ledger, dispatch_log=dispatch_log,
        api_url="http://127.0.0.1:8766", secret="probe-secret",
    )
    persisted = json.loads(dispatch_log.read_text(encoding="utf-8").splitlines()[0])

    assert result["eligible"] == 1
    assert result["dispatched"][0]["cycle_id"] == cycle_id
    assert observed["cycle_id"] == cycle_id
    assert observed["idempotency_key"] == "catedralx-economic-cycle:" + cycle_id
    assert observed["traceparent"].startswith(f"00-{trace_id}-")
    assert persisted["trace_id"] == trace_id
    assert persisted["status"] == "dispatched"


def test_result_store_write_and_read_preserve_cycle_and_trace(tmp_path):
    store = tmp_path / "results.jsonl"
    record = {
        "result_id": str(uuid4()),
        "status": "UNCERTAIN",
        "engine": "CatedralX",
        "decision": "hold",
        "evaluation_hash": "c" * 64,
        "evaluation_gate": "BLOCKED_UNCERTAINTY",
        "cycle_id": "result-cycle-probe",
        "evidence": [],
        "assumptions": [],
        "risks": [],
        "provenance": [],
        "trace_id": "d" * 32,
        "analysis_only": True,
        "orders_created": False,
        "orders_executed": False,
    }

    result_id = append_result(record, store)
    restored = get_result(result_id, store)

    assert restored is not None
    assert restored["cycle_id"] == record["cycle_id"]
    assert restored["trace_id"] == record["trace_id"]
    assert restored["orders_created"] is False
    assert restored["orders_executed"] is False
