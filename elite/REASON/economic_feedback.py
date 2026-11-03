"""Evidence-based business surplus allocation for CatedralX."""
from __future__ import annotations

import math
from typing import Any

DEFAULT_ALLOCATION = {"reinvestment": 0.50, "commons": 0.20, "reserves": 0.20, "shared_surplus": 0.10}

def _nonnegative_finite(name: str, value: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} debe ser un número finito no negativo.")
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser un número finito no negativo.") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{name} debe ser un número finito no negativo.")
    return parsed

def evaluate_economic_cycle(*, revenue_received: float, operating_costs: float, obligations: float, fair_compensation: float, currency: str, period: str, allocation: dict[str, float] | None = None) -> dict[str, Any]:
    """Calculate a proposed surplus allocation; it never moves money."""
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency es obligatoria (por ejemplo, MXN o USD).")
    if not isinstance(period, str) or not period.strip():
        raise ValueError("period es obligatorio (por ejemplo, 2026-10).")
    revenue = _nonnegative_finite("revenue_received", revenue_received)
    costs = _nonnegative_finite("operating_costs", operating_costs)
    obligations_value = _nonnegative_finite("obligations", obligations)
    compensation = _nonnegative_finite("fair_compensation", fair_compensation)
    rates = dict(DEFAULT_ALLOCATION if allocation is None else allocation)
    expected = set(DEFAULT_ALLOCATION)
    if set(rates) != expected:
        raise ValueError("allocation debe definir exactamente: reinvestment, commons, reserves, shared_surplus.")
    parsed_rates = {key: _nonnegative_finite(f"allocation.{key}", value) for key, value in rates.items()}
    if any(rate > 1 for rate in parsed_rates.values()):
        raise ValueError("Cada tasa de asignación debe estar entre 0 y 1.")
    if not math.isclose(sum(parsed_rates.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Las tasas de asignación deben sumar exactamente 1.")
    net_surplus = revenue - costs - obligations_value - compensation
    distributable = max(0.0, net_surplus)
    allocations = {key: round(distributable * rate, 2) for key, rate in parsed_rates.items()}
    allocations["reinvestment"] = round(allocations["reinvestment"] + round(distributable - sum(allocations.values()), 2), 2)
    return {
        "schema_version": "1.0",
        "status": "surplus_available" if net_surplus > 0 else ("break_even" if math.isclose(net_surplus, 0.0, abs_tol=0.005) else "deficit"),
        "currency": currency.strip().upper(), "period": period.strip(),
        "basis": "verified_received_revenue_minus_costs_obligations_and_fair_compensation",
        "revenue_received": round(revenue, 2), "operating_costs": round(costs, 2),
        "obligations": round(obligations_value, 2), "fair_compensation": round(compensation, 2),
        "net_surplus_before_allocation": round(net_surplus, 2), "distributable_surplus": round(distributable, 2),
        "allocation_rates": parsed_rates, "proposed_allocation": allocations,
        "allocation_reconciles": math.isclose(sum(allocations.values()), distributable, rel_tol=0.0, abs_tol=0.01),
        "policy_status": "illustrative_defaults_require_human_approval" if allocation is None else "user_supplied_rates_require_human_approval",
        "value_created_measurement": "not_provided", "social_impact_measurement": "not_provided",
        "money_moved": False, "payments_executed": False, "accounting_advice": False,
    }
