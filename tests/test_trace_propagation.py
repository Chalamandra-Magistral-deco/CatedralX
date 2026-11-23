"""Regression tests for end-to-end W3C trace ID and MSX provenance."""
from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from REASON import orchestrator


@pytest.fixture
def sensory():
    return SimpleNamespace(precio_historico=[100.0, 101.0], precio_actual=101.0, gap=0.01, inercia=0.2)


def make_state():
    return SimpleNamespace(
        percepcion_espacial={},
        cognicion={"operational_policy": {"hard_block": False}},
        decision="hold",
        free_energy=0.4,
        hamiltoniano=0.2,
        confianza=0.6,
        regimen="INDEFINIDO",
    )


def fake_energy_receipt(cycle_id):
    receipt = SimpleNamespace(transaction_id=f"cycle:{cycle_id}", reservoir="operational", amount=1.0, balance=9999.0)
    snapshot = {"state_of_charge": 0.999, "adaptive": SimpleNamespace(charge=2000.0)}
    return receipt, snapshot, {"sequence": 1, "record_hash": "b" * 64}

def test_execute_cycle_propagates_explicit_trace_id_and_provenance(monkeypatch, sensory):
    observed = {}
    state = make_state()

    def fake_think(data, prices, cycle_id, *, trace_id=None):
        observed.update(cycle_id=cycle_id, trace_id=trace_id)
        return state

    monkeypatch.setattr(orchestrator, "think", fake_think)
    monkeypatch.setattr(orchestrator, "consume_cycle_budget", fake_energy_receipt)
    result = orchestrator.execute_cycle(sensory, cycle_id="cycle-explicit-01", trace_id="a" * 32)

    assert result is state
    assert observed == {"cycle_id": "cycle-explicit-01", "trace_id": "a" * 32}
    assert result.percepcion_espacial["trace_id"] == "a" * 32
    assert result.cognicion["cycle_trace"]["cycle_id"] == "cycle-explicit-01"
    assert [record["vector"] for record in result.cognicion["provenance"]] == ["DSX", "RSX", "SCX", "DSX"]
    assert all(len(record["input_hash"]) == 64 for record in result.cognicion["provenance"])
    assert result.cognicion["resource_budget"]["status"] == "authorized"
    assert result.cognicion["resource_budget"]["unit"] == "virtual_compute_credit"
    assert result.cognicion["resource_budget"]["durability"] == "msx_hash_chained_jsonl"
    assert result.cognicion["resource_budget"]["ledger_sequence"] == 1


def test_execute_cycle_generates_trace_and_cycle_provenance(monkeypatch, sensory):
    observed = {}
    state = make_state()

    def fake_think(data, prices, cycle_id, *, trace_id=None):
        observed.update(cycle_id=cycle_id, trace_id=trace_id)
        return state

    monkeypatch.setattr(orchestrator, "think", fake_think)
    monkeypatch.setattr(orchestrator, "consume_cycle_budget", fake_energy_receipt)
    result = orchestrator.execute_cycle(sensory, cycle_id="cycle-generated-01")

    assert re.fullmatch(r"[0-9a-f]{32}", observed["trace_id"])
    assert observed["trace_id"] != "0" * 32
    assert result.percepcion_espacial["trace_id"] == observed["trace_id"]
    assert result.cognicion["cycle_trace"]["record_count"] == 4


@pytest.mark.parametrize("invalid", ["", "not-a-trace-id", "0" * 32, "A" * 32])
def test_execute_cycle_rejects_invalid_explicit_trace_id(sensory, invalid):
    with pytest.raises(ValueError, match="W3C trace ID"):
        orchestrator.execute_cycle(sensory, trace_id=invalid)
def test_execute_cycle_fails_closed_when_virtual_budget_is_exhausted(monkeypatch, sensory):
    called = {"think": False}

    def reject_budget(_cycle_id):
        raise ValueError("Reserva insuficiente; descarga rechazada")

    def fake_think(*args, **kwargs):
        called["think"] = True
        raise AssertionError("think no debe ejecutarse sin presupuesto")

    monkeypatch.setattr(orchestrator, "consume_cycle_budget", reject_budget)
    monkeypatch.setattr(orchestrator, "think", fake_think)
    with pytest.raises(ValueError, match="Reserva insuficiente"):
        orchestrator.execute_cycle(sensory, cycle_id="cycle-no-budget")
    assert called["think"] is False
