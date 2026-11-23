"""Process-local resource governor backed by the virtual vanadium battery.

Units are operator-configured compute-budget credits, not joules or physical
electrical energy. The ledger is process-local until a durable MSX store is
implemented; restarting the process resets this in-memory budget.
"""
from __future__ import annotations

import os
from functools import lru_cache

from ENERGY.virtual_vanadium_battery import EnergyReceipt, VirtualVanadiumBattery


def _env_float(name: str, default: str) -> float:
    raw = os.getenv(name, default)
    try:
        return float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser numérico") from exc


@lru_cache(maxsize=1)
def get_cycle_battery() -> VirtualVanadiumBattery:
    """Return the process-wide, environment-configured dual-reservoir budget."""
    operational_capacity = _env_float("CATEDRALX_ENERGY_OPERATIONAL_CAPACITY", "10000")
    adaptive_capacity = _env_float("CATEDRALX_ENERGY_ADAPTIVE_CAPACITY", "2000")
    return VirtualVanadiumBattery(
        operational_capacity=operational_capacity,
        adaptive_capacity=adaptive_capacity,
        operational_initial=_env_float("CATEDRALX_ENERGY_OPERATIONAL_INITIAL", str(operational_capacity)),
        adaptive_initial=_env_float("CATEDRALX_ENERGY_ADAPTIVE_INITIAL", str(adaptive_capacity)),
        max_discharge_per_cycle=_env_float("CATEDRALX_ENERGY_MAX_DISCHARGE", "1"),
        operational_reserve=_env_float("CATEDRALX_ENERGY_OPERATIONAL_RESERVE", "100"),
        adaptive_reserve=_env_float("CATEDRALX_ENERGY_ADAPTIVE_RESERVE", "50"),
    )


def consume_cycle_budget(cycle_id: str, *, amount: float | None = None) -> tuple[EnergyReceipt, dict[str, object]]:
    """Authorize one reasoning cycle by atomically spending operational credits."""
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id debe ser una cadena no vacía")
    cost = _env_float("CATEDRALX_ENERGY_CYCLE_COST", "1") if amount is None else amount
    battery = get_cycle_battery()
    receipt = battery.discharge(
        "operational", cost, transaction_id=f"cycle:{cycle_id}",
    )
    return receipt, battery.snapshot()