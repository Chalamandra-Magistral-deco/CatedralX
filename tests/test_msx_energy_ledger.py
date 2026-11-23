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
    assert path.read_bytes().count(b"\\n") == 2


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
    path.write_text(json.dumps(row) + "\\n")
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