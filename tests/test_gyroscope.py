"""Regression tests for the hardened gyroscope diagnostics."""
import numpy as np
import pytest

from REASON import gyroscope


@pytest.mark.parametrize(
    "prices",
    [
        [1.0, 2.0, True],
        [1.0, 2.0, float("nan")],
        [1.0, 2.0, float("inf")],
        [1.0, 2.0, 0.0],
        [1.0, 2.0, -1.0],
        [1.0, "2.0", 3.0],
        np.ones((2, 5)),
        "not-a-price-series",
    ],
)
def test_invalid_price_series_is_rejected(prices):
    with pytest.raises(ValueError):
        gyroscope.gyro_state(prices)


def test_short_series_returns_neutral_state_with_filter_key():
    result = gyroscope.gyro_state([100.0, 101.0, 102.0])
    assert result["fase"] == "CAOS"
    assert result["orientacion"] == "NEUTRO"
    assert result["_estado_filtro"] is None


@pytest.mark.parametrize(
    "state",
    [
        None,
        (np.array([0.0, 0.0]), np.eye(2)),
    ],
)
def test_short_series_accepts_absent_or_valid_filter_state(state):
    result = gyroscope.gyro_state([100.0, 101.0, 102.0], state)
    assert result["orientacion"] == "NEUTRO"


@pytest.mark.parametrize(
    "state",
    [
        (np.array([0.0]), np.eye(2)),
        (np.array([0.0, 0.0]), np.eye(3)),
        (np.array([0.0, float("nan")]), np.eye(2)),
        (np.array([0.0, 0.0]), np.array([[1.0, 2.0], [0.0, 1.0]])),
        (np.array([0.0, 0.0]), np.array([[1.0, 0.0], [0.0, -1.0]])),
    ],
)
def test_invalid_filter_state_is_rejected_even_for_short_series(state):
    with pytest.raises(ValueError):
        gyroscope.gyro_state([100.0, 101.0, 102.0], state)


@pytest.mark.parametrize("dt", [0.0, -1.0, float("nan"), float("inf"), True])
def test_ekf_rejects_invalid_dt(dt):
    with pytest.raises(ValueError):
        gyroscope.extended_kalman_filter(0.1, np.zeros(2), np.eye(2), dt=dt)


def test_ekf_returns_finite_symmetric_positive_covariance():
    x, p, omega = gyroscope.extended_kalman_filter(
        0.2, np.array([0.1, 0.0]), np.eye(2) * 0.1
    )
    assert x.shape == (2,)
    assert p.shape == (2, 2)
    assert np.all(np.isfinite(x))
    assert np.all(np.isfinite(p))
    assert np.allclose(p, p.T)
    assert np.min(np.linalg.eigvalsh(p)) >= -1e-10
    assert omega == pytest.approx(float(x[0]))


def test_gyro_outputs_bounded_metrics_and_reusable_filter_state(monkeypatch):
    hurst_values = iter([0.8, 0.6])
    monkeypatch.setattr(
        gyroscope.hurst,
        "hurst_exponent",
        lambda *args, **kwargs: next(hurst_values),
    )
    prices = np.linspace(100.0, 110.0, 60).tolist()
    result = gyroscope.gyro_state(prices)

    assert result["fase"] == "TENDENCIA"
    assert result["orientacion"] == "ALCISTA"
    for key in ("omega", "precesion", "estabilidad", "entropia", "confianza"):
        assert np.isfinite(result[key])
    assert -1.0 <= result["omega"] <= 1.0
    assert 0.0 <= result["estabilidad"] <= 1.0
    assert 0.0 <= result["entropia"] <= 1.0
    assert 0.0 <= result["confianza"] <= 1.0

    next_values = iter([0.75, 0.65])
    monkeypatch.setattr(
        gyroscope.hurst,
        "hurst_exponent",
        lambda *args, **kwargs: next(next_values),
    )
    next_result = gyroscope.gyro_state(prices, result["_estado_filtro"])
    assert next_result["_estado_filtro"][0].shape == (2,)
    assert next_result["_estado_filtro"][1].shape == (2, 2)


@pytest.mark.parametrize("hurst_value", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_hurst_estimate_is_rejected(monkeypatch, hurst_value):
    monkeypatch.setattr(
        gyroscope.hurst, "hurst_exponent", lambda *args, **kwargs: hurst_value
    )
    with pytest.raises(ValueError):
        gyroscope.gyro_state(np.linspace(100.0, 110.0, 60).tolist())
