"""Regression tests for the MCX reserve estimator."""

import math

import pytest

from MCX.OPTIMIZE.reserve_estimator import estimar_reserva


def test_estimates_reserve_with_default_rate() -> None:
    result = estimar_reserva(1000)

    assert result["ingreso"] == 1000.0
    assert result["tasa_configurada"] == 0.02
    assert result["reserva_estimada"] == 20.0
    assert "no determina" in result["disclaimer"]


@pytest.mark.parametrize(
    ("ingreso", "tasa", "expected"),
    [
        (1000, 0.10, 100.0),
        (1250.50, 0.04, 50.02),
        (0, 0.02, 0.0),
        (100, 0, 0.0),
        (100, 1, 100.0),
    ],
)
def test_estimates_reserve_for_valid_boundaries(
    ingreso: float, tasa: float, expected: float
) -> None:
    assert estimar_reserva(ingreso, tasa)["reserva_estimada"] == expected


@pytest.mark.parametrize("value", [True, False, "100", None, object()])
def test_rejects_non_numeric_and_boolean_values(value) -> None:
    with pytest.raises(TypeError):
        estimar_reserva(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_income(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        estimar_reserva(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_rate(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        estimar_reserva(100, value)


def test_rejects_extremely_large_integer_without_overflowing() -> None:
    with pytest.raises(ValueError, match="finite"):
        estimar_reserva(10**10000)


@pytest.mark.parametrize("ingreso", [-0.01, -1, -100])
def test_rejects_negative_income(ingreso: float) -> None:
    with pytest.raises(ValueError, match="ingreso must be >= 0"):
        estimar_reserva(ingreso)


@pytest.mark.parametrize("tasa", [-0.01, 1.01, -1, 2])
def test_rejects_rate_outside_unit_interval(tasa: float) -> None:
    with pytest.raises(ValueError, match="tasa must be between 0 and 1"):
        estimar_reserva(100, tasa)
