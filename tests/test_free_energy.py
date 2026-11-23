import pytest

from REASON.free_energy import free_energy, prediccion_interna


def test_free_energy_combines_observed_surprise_terms():
    # (0.2 return + 0.2 gap) * 1.2 incoherence * 2.5
    assert free_energy(
        prediccion_tendencia=0.8,
        realidad_gap=0.001,
        inercia_observada=0.6,
        retorno_actual=0.02,
        coherencia_previa=0.8,
    ) == pytest.approx(1.2)


def test_free_energy_is_bounded_to_zero_and_twenty():
    assert free_energy(0.5, 0.0, 0.0, 0.0, 1.0) == 0.0
    assert free_energy(0.5, 1.0, 0.0, 10.0, 0.0) == 20.0


def test_internal_prediction_is_bounded_and_uses_cross_ratio():
    assert prediccion_interna(0.5, 0.0) == 0.0
    assert prediccion_interna(0.75, 0.0) == pytest.approx(0.5)
    assert prediccion_interna(0.75, 5.0) == pytest.approx(0.25)
    assert 0.0 <= prediccion_interna(1.0, 100.0) <= 1.0


import math
import pytest

from REASON.free_energy import free_energy, prediccion_interna


@pytest.mark.parametrize("kwargs", [
    {"prediccion_tendencia": 1.1, "realidad_gap": 0.0, "inercia_observada": 0.0},
    {"prediccion_tendencia": 0.5, "realidad_gap": -0.1, "inercia_observada": 0.0},
    {"prediccion_tendencia": 0.5, "realidad_gap": 0.0, "inercia_observada": 0.0, "coherencia_previa": 1.1},
    {"prediccion_tendencia": math.nan, "realidad_gap": 0.0, "inercia_observada": 0.0},
])
def test_free_energy_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        free_energy(**kwargs)


@pytest.mark.parametrize("hurst", [-0.1, 1.1, math.inf, math.nan])
def test_internal_prediction_rejects_invalid_hurst(hurst):
    with pytest.raises(ValueError):
        prediccion_interna(hurst, 0.0)