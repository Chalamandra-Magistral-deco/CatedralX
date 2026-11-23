import json

import pytest

from MSX.energy_ledger import EnergyLedger


def test_energy_ledger_appends_hash_chained_jsonl_and_reloads(tmp_path):
    path = tmp_path / "energy.jsonl"
    ledger = EnergyLedger(path)
    first = ledger.append({"transaction_id": "tx-1", "amount": 1.0})
    second = ledger.append({"transaction_id": "tx-2", "amount": 2.0})
    restored = EnergyLedger(path).read()
    assert [row["sequence"] for row in restored] == [1, 2]
    assert second["previous_hash"] == first["record_hash"]
    assert path.read_bytes().count(b"\n") == 2


def test_energy_ledger_rejects_duplicate_transaction(tmp_path):
    ledger = EnergyLedger(tmp_path / "energy.jsonl")
    ledger.append({"transaction_id": "same", "amount": 1.0})
    with pytest.raises(ValueError, match="duplicado"):
        ledger.append({"transaction_id": "same", "amount": 1.0})


def test_energy_ledger_fails_closed_on_tampering(tmp_path):
    path = tmp_path / "energy.jsonl"
    ledger = EnergyLedger(path)
    ledger.append({"transaction_id": "tx-1", "amount": 1.0})
    row = json.loads(path.read_text().strip())
    row["amount"] = 99.0
    path.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="hash inválido"):
        ledger.read()


def test_energy_ledger_rejects_incomplete_trailing_record(tmp_path):
    path = tmp_path / "energy.jsonl"
    ledger = EnergyLedger(path)
    ledger.append({"transaction_id": "tx-1", "amount": 1.0})
    with path.open("ab") as stream:
        stream.write(b"partial")
    with pytest.raises(ValueError, match="incompleta"):
        ledger.read()

from ENERGY.resource_governor import consume_adaptive_budget, consume_cycle_budget, energy_budget_snapshot


def configure_budget(monkeypatch, tmp_path):
    monkeypatch.setenv("CATEDRALX_ENERGY_LEDGER_PATH", str(tmp_path / "energy.jsonl"))
    monkeypatch.setenv("CATEDRALX_ENERGY_OPERATIONAL_CAPACITY", "10")
    monkeypatch.setenv("CATEDRALX_ENERGY_ADAPTIVE_CAPACITY", "5")
    monkeypatch.setenv("CATEDRALX_ENERGY_OPERATIONAL_INITIAL", "10")
    monkeypatch.setenv("CATEDRALX_ENERGY_ADAPTIVE_INITIAL", "5")
    monkeypatch.setenv("CATEDRALX_ENERGY_MAX_DISCHARGE", "2")
    monkeypatch.setenv("CATEDRALX_ENERGY_OPERATIONAL_RESERVE", "2")
    monkeypatch.setenv("CATEDRALX_ENERGY_ADAPTIVE_RESERVE", "1")


def test_governor_reloads_operational_balance_and_keeps_adaptive_reserve(monkeypatch, tmp_path):
    configure_budget(monkeypatch, tmp_path)
    receipt, snapshot, record = consume_cycle_budget("cycle-1", amount=2)
    assert receipt.balance == 8
    assert record["sequence"] == 1
    assert snapshot["adaptive"].charge == 5
    restored = energy_budget_snapshot()
    assert restored["operational"].charge == 8
    assert restored["adaptive"].charge == 5


def test_adaptive_budget_is_separate_and_durable(monkeypatch, tmp_path):
    configure_budget(monkeypatch, tmp_path)
    consume_cycle_budget("cycle-1", amount=1)
    receipt, snapshot, record = consume_adaptive_budget("simulation-1", amount=2)
    assert receipt.reservoir == "adaptive"
    assert receipt.balance == 3
    assert snapshot["operational"].charge == 9
    assert record["sequence"] == 2
    restored = energy_budget_snapshot()
    assert restored["adaptive"].charge == 3


def test_governor_blocks_spend_below_reserve(monkeypatch, tmp_path):
    configure_budget(monkeypatch, tmp_path)
    consume_cycle_budget("cycle-1", amount=2)
    consume_cycle_budget("cycle-2", amount=2)
    consume_cycle_budget("cycle-3", amount=2)
    with pytest.raises(ValueError, match="Reserva insuficiente"):
        consume_cycle_budget("cycle-4", amount=2)
    assert energy_budget_snapshot()["operational"].charge == 4