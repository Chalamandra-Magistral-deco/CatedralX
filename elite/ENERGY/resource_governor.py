"""MSX-backed process and cross-process resource governor.

Credits are abstract compute quotas, not joules or physical electrical energy.
Every authorization is replayed from and committed to the durable MSX ledger.
Ledger corruption, a broken hash chain or an inconsistent balance fails closed.
"""
from __future__ import annotations

import os

from ENERGY.virtual_vanadium_battery import EnergyReceipt, VirtualVanadiumBattery
from MSX.energy_ledger import EnergyLedger


def _env_float(name: str, default: str) -> float:
    raw = os.getenv(name, default)
    try: return float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser numérico") from exc


def _new_battery() -> VirtualVanadiumBattery:
    op = _env_float("CATEDRALX_ENERGY_OPERATIONAL_CAPACITY", "10000")
    ad = _env_float("CATEDRALX_ENERGY_ADAPTIVE_CAPACITY", "2000")
    return VirtualVanadiumBattery(
        operational_capacity=op, adaptive_capacity=ad,
        operational_initial=_env_float("CATEDRALX_ENERGY_OPERATIONAL_INITIAL", str(op)),
        adaptive_initial=_env_float("CATEDRALX_ENERGY_ADAPTIVE_INITIAL", str(ad)),
        max_discharge_per_cycle=_env_float("CATEDRALX_ENERGY_MAX_DISCHARGE", "1"),
        operational_reserve=_env_float("CATEDRALX_ENERGY_OPERATIONAL_RESERVE", "100"),
        adaptive_reserve=_env_float("CATEDRALX_ENERGY_ADAPTIVE_RESERVE", "50"),
    )


def _replay(records: list[dict[str, object]]) -> VirtualVanadiumBattery:
    battery = _new_battery()
    for row in records:
        if row.get("event_type") != "virtual_energy_transaction":
            continue
        operation, reservoir = row.get("operation"), row.get("reservoir")
        amount, txid = row.get("amount"), row.get("transaction_id")
        if operation == "discharge": receipt = battery.discharge(reservoir, amount, transaction_id=txid)
        elif operation == "charge": receipt = battery.charge(reservoir, amount, transaction_id=txid)
        else: raise ValueError("MSX energy ledger: operación desconocida")
        if abs(receipt.balance - float(row.get("balance_after"))) > 1e-9:
            raise ValueError("MSX energy ledger: saldo reconstruido inconsistente")
    return battery


def _consume(cycle_id: str, reservoir: str, amount: float | None) -> tuple[EnergyReceipt, dict[str, object], dict[str, object]]:
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id debe ser una cadena no vacía")
    cost = _env_float("CATEDRALX_ENERGY_CYCLE_COST", "1") if amount is None else amount
    ledger = EnergyLedger()
    transaction_id = f"cycle:{cycle_id}:{reservoir}"
    result: dict[str, object] = {}
    def authorize(records):
        battery = _replay(records)
        receipt = battery.discharge(reservoir, cost, transaction_id=transaction_id)
        snapshot = battery.snapshot()
        result["receipt"] = receipt
        result["snapshot"] = snapshot
        return {
            "event_type": "virtual_energy_transaction",
            "transaction_id": receipt.transaction_id,
            "cycle_id": cycle_id,
            "operation": receipt.operation,
            "reservoir": receipt.reservoir,
            "amount": receipt.amount,
            "balance_after": receipt.balance,
            "timestamp": receipt.timestamp,
            "unit": "virtual_compute_credit",
        }
    record = ledger.transact(authorize)
    return result["receipt"], result["snapshot"], record


def consume_cycle_budget(cycle_id: str, *, amount: float | None = None):
    """Spend operational credits; no reasoning cycle starts without this authorization."""
    return _consume(cycle_id, "operational", amount)


def consume_adaptive_budget(cycle_id: str, *, amount: float | None = None):
    """Spend adaptive credits for explicitly invoked learning/simulation work only."""
    return _consume(cycle_id, "adaptive", amount)


def energy_budget_snapshot() -> dict[str, object]:
    """Return balances reconstructed from the verified durable ledger."""
    ledger = EnergyLedger()
    return _replay(ledger.read()).snapshot()