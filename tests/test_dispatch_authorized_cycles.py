from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ELITE = ROOT / "elite"
if str(ELITE) not in sys.path:
    sys.path.insert(0, str(ELITE))

SPEC = importlib.util.spec_from_file_location(
    "dispatch_authorized_cycles", ELITE / "bin" / "dispatch_authorized_cycles.py"
)
assert SPEC and SPEC.loader
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)
from FEX.GOVERNANCE.economic_cycle import registrar_evento  # noqa: E402


def _authorized_cycle(path: Path) -> str:
    cycle_id = registrar_evento(
        "measure",
        {
            "metric": "qualified_leads",
            "source": "synthetic_test",
            "period": "2026-10",
            "unit": "leads",
            "formula": "count_unique",
            "value": 3,
            "observed_at": datetime.now(UTC).isoformat(),
        },
        path=path,
    )
    registrar_evento(
        "evaluate", {"assessment": "test assessment", "evidence": "synthetic only"},
        path=path, cycle_id=cycle_id,
    )
    registrar_evento(
        "propose", {
            "proposal": "analyze synthetic demand",
            "expected_outcome": "candidate for review",
            "verification_plan": "compare the next period",
        }, path=path, cycle_id=cycle_id,
    )
    registrar_evento(
        "authorize", {"approved": True, "approver": "test-owner", "rationale": "analysis only",
                      "identity_assertion": {"signed": "test-only-assertion"}},
        path=path, cycle_id=cycle_id,
    )
    return cycle_id


def _inject_test_identity_verifier(monkeypatch):
    from AEX.DECISION import ordenes
    monkeypatch.setattr(
        ordenes, "APPROVER_IDENTITY_VERIFIER",
        lambda assertion, decision, price: {
            "verified": assertion == {"signed": "test-only-assertion"},
            "subject": "test-owner",
            "permissions": ["economic_cycle_authorize"],
        },
    )


def test_scan_dispatches_authorized_cycle_once_with_idempotency(monkeypatch, tmp_path):
    _inject_test_identity_verifier(monkeypatch)
    ledger = tmp_path / "impact_cycle.jsonl"
    dispatch_log = tmp_path / "dispatches.jsonl"
    cycle_id = _authorized_cycle(ledger)
    calls = []

    def fake_dispatch(objective, payload, api_url, secret, timeout=5.0, idempotency_key=None, traceparent=None):
        calls.append({"objective": objective, "payload": payload, "api_url": api_url,
                      "secret": secret, "key": idempotency_key})
        return {"status": "queued", "run_id": "run-test", "task_id": "task-test", "trace_id": "a" * 32}

    monkeypatch.setattr(scanner, "dispatch_task", fake_dispatch)
    first = scanner.scan_and_dispatch(
        ledger=ledger, dispatch_log=dispatch_log, api_url="http://127.0.0.1:8766",
        secret="test-secret-only",
    )
    assert first["eligible"] == 1
    assert len(first["dispatched"]) == 1
    assert first["dispatched"][0]["cycle_id"] == cycle_id
    assert calls[0]["key"] == "catedralx-economic-cycle:" + cycle_id
    assert calls[0]["objective"] == "catedralx_economic_proposal_review"
    assert first["orders_created"] is False
    assert first["trading_enabled"] is False

    second = scanner.scan_and_dispatch(
        ledger=ledger, dispatch_log=dispatch_log, api_url="http://127.0.0.1:8766",
        secret="test-secret-only",
    )
    assert second["eligible"] == 1
    assert second["dispatched"] == []
    assert second["already_dispatched"] == 1
    assert len(calls) == 1


def test_scan_does_not_dispatch_cycle_without_human_authorization(monkeypatch, tmp_path):
    ledger = tmp_path / "impact_cycle.jsonl"
    dispatch_log = tmp_path / "dispatches.jsonl"
    cycle_id = registrar_evento(
        "measure",
        {"metric": "x", "source": "synthetic", "period": "2026-10", "unit": "count",
         "formula": "count", "value": 1, "observed_at": datetime.now(UTC).isoformat()},
        path=ledger,
    )
    registrar_evento("evaluate", {"assessment": "test", "evidence": "synthetic"}, path=ledger, cycle_id=cycle_id)
    registrar_evento("propose", {"proposal": "p", "expected_outcome": "o", "verification_plan": "v"}, path=ledger, cycle_id=cycle_id)
    calls = []
    monkeypatch.setattr(scanner, "dispatch_task", lambda *args, **kwargs: calls.append(args))
    result = scanner.scan_and_dispatch(
        ledger=ledger, dispatch_log=dispatch_log, api_url="http://127.0.0.1:8766", secret="test-secret-only"
    )
    assert result["eligible"] == 0
    assert result["dispatched"] == []
    assert calls == []


def test_scan_requires_dedicated_secret(tmp_path):
    with pytest.raises(ValueError, match="CHALAMANDRA_CATEDRALX_JWT_SECRET"):
        scanner.scan_and_dispatch(
            ledger=tmp_path / "missing.jsonl", dispatch_log=tmp_path / "dispatches.jsonl",
            api_url="http://127.0.0.1:8766", secret="",
        )
