"""Regression tests for numeric fail-closed dynamic constraints."""
from __future__ import annotations

from REASON.dynamic_constraints import (
    DynamicConstraintInputs,
    evaluate_dynamic_constraints,
)


def _valid_inputs(**overrides):
    values = {
        "reinvestment_surplus": 10.0,
        "entropy_rate": 1.0,
        "entropy_time_scale": 2.0,
        "loop_gain": 0.7,
        "signal_count": 4,
        "optimal_signal_count": 5,
        "exposure": 0.2,
        "max_exposure": 0.5,
        "resilience": 0.9,
        "minimum_resilience": 0.7,
    }
    values.update(overrides)
    return DynamicConstraintInputs(**values)


def test_extremely_large_integer_is_invalid_without_raising():
    result = evaluate_dynamic_constraints(
        _valid_inputs(reinvestment_surplus=10**10000)
    )
    assert result["growth_allowed"] is False
    assert "DATOS_INVALIDOS" in result["issues"]
    assert "reinvestment_surplus" in result["invalid_metrics"]


def test_extremely_large_optional_integer_is_invalid_without_raising():
    result = evaluate_dynamic_constraints(
        _valid_inputs(accumulated_noise=10**10000)
    )
    assert result["growth_allowed"] is False
    assert "DATOS_INVALIDOS" in result["issues"]
    assert "accumulated_noise" in result["invalid_metrics"]


def test_finite_inputs_with_overflowing_entropy_product_fail_closed():
    result = evaluate_dynamic_constraints(
        _valid_inputs(
            reinvestment_surplus=1e308,
            entropy_rate=1e308,
            entropy_time_scale=1e308,
        )
    )
    assert result["growth_allowed"] is False
    assert result["entropy_constraint_ok"] is False
    assert result["calculation_errors"] == ["ENTROPY_REQUIREMENT_NON_FINITE"]
    assert "CALCULO_NO_FINITO" in result["issues"]


def test_optional_metrics_are_explicitly_observational_not_growth_gates():
    result = evaluate_dynamic_constraints(
        _valid_inputs(
            dominant_signal_weight=0.01,
            minimum_confidence=0.99,
            degradation_rate=1000.0,
            accumulated_noise=1000.0,
        )
    )
    assert result["growth_allowed"] is True
    assert result["observational_metrics"] == {
        "dominant_signal_weight": 0.01,
        "minimum_confidence": 0.99,
        "degradation_rate": 1000.0,
        "accumulated_noise": 1000.0,
    }


def test_optional_metrics_still_reject_invalid_domains():
    for field, value in (
        ("dominant_signal_weight", -0.1),
        ("minimum_confidence", 1.1),
        ("degradation_rate", -0.1),
        ("accumulated_noise", float("inf")),
    ):
        result = evaluate_dynamic_constraints(_valid_inputs(**{field: value}))
        assert result["growth_allowed"] is False
        assert "DATOS_INVALIDOS" in result["issues"]
        assert field in result["invalid_metrics"]
