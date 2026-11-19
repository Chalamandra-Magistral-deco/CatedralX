"""Validation and feedback-stability tests for SCX surprise diagnostics."""
from __future__ import annotations

import math

import pytest

from elite.REASON.free_energy import (
    MAX_FREE_ENERGY,
    coherencia_desde_energia_previa,
    free_energy,
    prediccion_interna,
)


def test_free_energy_preserves_existing_formula_with_valid_inputs():
    result = free_energy(
        prediccion_tendencia=0.75,
        realidad_gap=0.001,
        inercia_observada=0.0,
        retorno_actual=0.01,
        coherencia_previa=0.5,
    )
    # return=0.1, gap=0.2, inertia=0.25; multiplier=1.5 * 2.5
    assert result == pytest.approx(2.0625)


def test_free_energy_is_bounded_and_finite_for_extreme_finite_return():
    result = free_energy(0.5, 0.0, 0.0, retorno_actual=1e308, coherencia_previa=0.0)
    assert result == MAX_FREE_ENERGY
    assert math.isfinite(result)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"prediccion_tendencia": float("nan")}, "prediccion_tendencia"),
        ({"realidad_gap": float("inf")}, "realidad_gap"),
        ({"inercia_observada": True}, "inercia_observada"),
        ({"retorno_actual": "0.01"}, "retorno_actual"),
        ({"coherencia_previa": -0.1}, "coherencia_previa"),
        ({"prediccion_tendencia": 1.1}, "prediccion_tendencia"),
        ({"realidad_gap": -0.01}, "realidad_gap"),
        ({"inercia_observada": 1.1}, "inercia_observada"),
        ({"coherencia_previa": 1.1}, "coherencia_previa"),
    ],
)
def test_free_energy_rejects_invalid_inputs(kwargs, message):
    values = {
        "prediccion_tendencia": 0.5,
        "realidad_gap": 0.0,
        "inercia_observada": 0.0,
        "retorno_actual": 0.0,
        "coherencia_previa": 0.5,
    }
    values.update(kwargs)
    with pytest.raises(ValueError, match=message):
        free_energy(**values)


def test_lower_prior_coherence_amplifies_the_same_observed_surprise():
    inputs = {
        "prediccion_tendencia": 0.7,
        "realidad_gap": 0.002,
        "inercia_observada": 0.1,
        "retorno_actual": 0.02,
    }
    high_coherence = free_energy(**inputs, coherencia_previa=1.0)
    low_coherence = free_energy(**inputs, coherencia_previa=0.25)
    assert low_coherence > high_coherence


def test_previous_energy_maps_to_bounded_feedback_coherence():
    assert coherencia_desde_energia_previa(0.0) == 1.0
    assert coherencia_desde_energia_previa(10.0) == 0.5
    assert coherencia_desde_energia_previa(20.0) == 0.0


@pytest.mark.parametrize("value", [-0.01, 20.01, float("nan"), float("inf"), True])
def test_feedback_coherence_rejects_invalid_previous_energy(value):
    with pytest.raises(ValueError):
        coherencia_desde_energia_previa(value)


def test_feedback_recovers_after_a_transient_shock():
    shock = free_energy(
        prediccion_tendencia=0.5,
        realidad_gap=0.0,
        inercia_observada=0.0,
        retorno_actual=3.0,
        coherencia_previa=1.0,
    )
    assert shock == MAX_FREE_ENERGY

    after_shock_coherence = coherencia_desde_energia_previa(shock)
    quiet_cycle = free_energy(
        prediccion_tendencia=0.5,
        realidad_gap=0.0,
        inercia_observada=0.0,
        retorno_actual=0.0,
        coherencia_previa=after_shock_coherence,
    )
    assert quiet_cycle == 0.0
    assert coherencia_desde_energia_previa(quiet_cycle) == 1.0


def test_prediccion_interna_is_bounded_and_rejects_invalid_hurst():
    assert 0.0 <= prediccion_interna(0.9, 1.5) <= 1.0
    with pytest.raises(ValueError, match="hurst"):
        prediccion_interna(float("nan"), 1.0)
    with pytest.raises(ValueError, match="hurst"):
        prediccion_interna(1.1, 1.0)
