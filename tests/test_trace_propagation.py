"""Regression tests for end-to-end W3C trace ID propagation."""
from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from REASON import orchestrator


@pytest.fixture
def sensory():
    return SimpleNamespace(precio_historico=[100.0, 101.0])


def test_execute_cycle_propagates_explicit_trace_id(monkeypatch, sensory):
    observed = {}
    state = SimpleNamespace(percepcion_espacial={})

    def fake_think(data, prices, cycle_id, *, trace_id=None):
        observed.update(cycle_id=cycle_id, trace_id=trace_id)
        return state

    monkeypatch.setattr(orchestrator, "think", fake_think)

    result = orchestrator.execute_cycle(
        sensory,
        cycle_id="cycle-explicit-01",
        trace_id="a" * 32,
    )

    assert result is state
    assert observed == {
        "cycle_id": "cycle-explicit-01",
        "trace_id": "a" * 32,
    }
    assert result.percepcion_espacial["trace_id"] == "a" * 32


def test_execute_cycle_generates_valid_trace_id_when_missing(monkeypatch, sensory):
    observed = {}
    state = SimpleNamespace(percepcion_espacial={})

    def fake_think(data, prices, cycle_id, *, trace_id=None):
        observed.update(cycle_id=cycle_id, trace_id=trace_id)
        return state

    monkeypatch.setattr(orchestrator, "think", fake_think)

    result = orchestrator.execute_cycle(sensory, cycle_id="cycle-generated-01")

    assert re.fullmatch(r"[0-9a-f]{32}", observed["trace_id"])
    assert observed["trace_id"] != "0" * 32
    assert result.percepcion_espacial["trace_id"] == observed["trace_id"]


@pytest.mark.parametrize("invalid", ["", "not-a-trace-id", "0" * 32, "A" * 32])
def test_execute_cycle_rejects_invalid_explicit_trace_id(sensory, invalid):
    with pytest.raises(ValueError, match="W3C trace ID"):
        orchestrator.execute_cycle(sensory, trace_id=invalid)
