from __future__ import annotations
import pytest
from REASON.economic_feedback import evaluate_economic_cycle


def test_surplus_allocation_reconciles_without_moving_money():
    result = evaluate_economic_cycle(revenue_received=1000, operating_costs=300, obligations=100, fair_compensation=200, currency="mxn", period="2026-10")
    assert result["status"] == "surplus_available"
    assert result["net_surplus_before_allocation"] == 400
    assert sum(result["proposed_allocation"].values()) == 400
    assert result["allocation_reconciles"] is True
    assert result["currency"] == "MXN"
    assert result["money_moved"] is False
    assert result["payments_executed"] is False
    assert result["value_created_measurement"] == "not_provided"


def test_deficit_is_not_hidden_or_allocated():
    result = evaluate_economic_cycle(revenue_received=100, operating_costs=120, obligations=20, fair_compensation=10, currency="MXN", period="2026-10")
    assert result["status"] == "deficit"
    assert result["net_surplus_before_allocation"] == -50
    assert result["distributable_surplus"] == 0
    assert sum(result["proposed_allocation"].values()) == 0


@pytest.mark.parametrize("field,value", [("revenue_received", -1), ("operating_costs", float("nan")), ("obligations", float("inf")), ("fair_compensation", True)])
def test_invalid_money_values_are_rejected(field, value):
    values = dict(revenue_received=100, operating_costs=20, obligations=10, fair_compensation=10, currency="MXN", period="2026-10")
    values[field] = value
    with pytest.raises(ValueError):
        evaluate_economic_cycle(**values)


def test_allocation_rates_must_sum_to_one():
    with pytest.raises(ValueError, match="sumar exactamente 1"):
        evaluate_economic_cycle(revenue_received=100, operating_costs=0, obligations=0, fair_compensation=0, currency="MXN", period="2026-10", allocation={"reinvestment": 0.5, "commons": 0.2, "reserves": 0.2, "shared_surplus": 0.2})


def test_currency_and_period_are_required():
    with pytest.raises(ValueError, match="currency"):
        evaluate_economic_cycle(revenue_received=100, operating_costs=0, obligations=0, fair_compensation=0, currency="", period="2026-10")
