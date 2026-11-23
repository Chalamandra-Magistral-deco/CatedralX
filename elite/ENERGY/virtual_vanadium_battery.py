"""Virtual vanadium-flow-inspired resource battery for CatedralX.

This is a software resource budget, not a physical/electrochemical battery.
Energy units are abstract compute-budget units. Capacity and power are kept
separate, and resources are never replenished without an explicit charge.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import threading
import time
import uuid
from typing import Literal

ReservoirName = Literal["operational", "adaptive"]


def _finite_non_negative(name: str, value: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} debe ser un número finito no negativo")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser un número finito no negativo") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} debe ser un número finito no negativo")
    return result


@dataclass(frozen=True)
class Reservoir:
    capacity: float
    charge: float

    @property
    def state_of_charge(self) -> float:
        return 0.0 if self.capacity == 0 else self.charge / self.capacity


@dataclass(frozen=True)
class EnergyReceipt:
    transaction_id: str
    operation: str
    reservoir: ReservoirName
    amount: float
    balance: float
    timestamp: float


class VirtualVanadiumBattery:
    """Thread-safe dual-reservoir budget with power, reserve and audit controls.

    operational funds required request/analysis work. adaptive funds optional
    exploration/simulation. Both are virtual accounting reservoirs.
    """

    def __init__(
        self, *, operational_capacity: float, adaptive_capacity: float,
        operational_initial: float | None = None, adaptive_initial: float | None = None,
        max_discharge_per_cycle: float, operational_reserve: float = 0.0,
        adaptive_reserve: float = 0.0,
    ) -> None:
        self._lock = threading.RLock()
        self._capacities = {
            "operational": _finite_non_negative("operational_capacity", operational_capacity),
            "adaptive": _finite_non_negative("adaptive_capacity", adaptive_capacity),
        }
        self._charges = {
            "operational": self._initial("operational_initial", operational_initial, self._capacities["operational"]),
            "adaptive": self._initial("adaptive_initial", adaptive_initial, self._capacities["adaptive"]),
        }
        self._reserves = {
            "operational": _finite_non_negative("operational_reserve", operational_reserve),
            "adaptive": _finite_non_negative("adaptive_reserve", adaptive_reserve),
        }
        if any(self._reserves[k] > self._capacities[k] for k in self._capacities):
            raise ValueError("La reserva mínima no puede superar la capacidad del depósito")
        self.max_discharge_per_cycle = _finite_non_negative("max_discharge_per_cycle", max_discharge_per_cycle)
        self._ledger: list[EnergyReceipt] = []
        self._transaction_ids: set[str] = set()

    @staticmethod
    def _initial(name: str, value: float | None, capacity: float) -> float:
        charge = capacity if value is None else _finite_non_negative(name, value)
        if charge > capacity:
            raise ValueError(f"{name} no puede superar la capacidad")
        return charge

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            reservoirs = {name: Reservoir(self._capacities[name], self._charges[name]) for name in self._capacities}
            total_capacity = sum(self._capacities.values())
            total_charge = sum(self._charges.values())
            return {
                "status": "available" if total_charge > 0 else "depleted",
                "operational": reservoirs["operational"],
                "adaptive": reservoirs["adaptive"],
                "total_capacity": total_capacity,
                "total_charge": total_charge,
                "state_of_charge": 0.0 if total_capacity == 0 else total_charge / total_capacity,
                "max_discharge_per_cycle": self.max_discharge_per_cycle,
                "ledger_entries": len(self._ledger),
            }

    def _record(self, operation: str, reservoir: ReservoirName, amount: float, transaction_id: str | None) -> EnergyReceipt:
        txid = transaction_id or uuid.uuid4().hex
        if not isinstance(txid, str) or not txid.strip():
            raise ValueError("transaction_id debe ser una cadena no vacía")
        if txid in self._transaction_ids:
            raise ValueError("transaction_id duplicado")
        self._transaction_ids.add(txid)
        receipt = EnergyReceipt(txid, operation, reservoir, amount, self._charges[reservoir], time.time())
        self._ledger.append(receipt)
        return receipt

    def discharge(self, reservoir: ReservoirName, amount: float, *, transaction_id: str | None = None) -> EnergyReceipt:
        requested = _finite_non_negative("amount", amount)
        if reservoir not in self._charges:
            raise ValueError("depósito desconocido")
        with self._lock:
            if requested > self.max_discharge_per_cycle:
                raise ValueError("Demanda supera la potencia máxima por ciclo")
            available = self._charges[reservoir] - self._reserves[reservoir]
            if requested > available:
                raise ValueError("Reserva insuficiente; descarga rechazada")
            self._charges[reservoir] -= requested
            return self._record("discharge", reservoir, requested, transaction_id)

    def charge(self, reservoir: ReservoirName, amount: float, *, transaction_id: str | None = None) -> EnergyReceipt:
        supplied = _finite_non_negative("amount", amount)
        if reservoir not in self._charges:
            raise ValueError("depósito desconocido")
        with self._lock:
            remaining = self._capacities[reservoir] - self._charges[reservoir]
            if supplied > remaining:
                raise ValueError("La carga supera la capacidad disponible")
            self._charges[reservoir] += supplied
            return self._record("charge", reservoir, supplied, transaction_id)

    def ledger(self) -> tuple[EnergyReceipt, ...]:
        with self._lock:
            return tuple(self._ledger)