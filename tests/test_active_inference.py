import math

import numpy as np
import pytest

from REASON.active_inference import ActiveInferenceEngine, MIN_SIGMA


def test_inferir_preserves_two_value_tuple_api():
    engine = ActiveInferenceEngine()
    result = engine.inferir([0.01, 0.02, -0.01], 102.0, 100.0)

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(math.isfinite(value) for value in result)
    assert result[0] >= 0.0
    assert result[1] >= 0.0


def test_detailed_result_exposes_kl_surprise_and_free_energy():
    engine = ActiveInferenceEngine()
    result = engine.inferir_detallado([0.01, 0.02, -0.01], 102.0, 100.0)

    assert result.kl_divergence >= 0.0
    assert math.isfinite(result.surprise)
    assert result.variational_free_energy >= 0.0
    assert result.posterior_sigma >= MIN_SIGMA
    assert result.observed_log_return == pytest.approx(math.log(1.02))


def test_constant_returns_use_positive_variance_floor():
    engine = ActiveInferenceEngine()
    result = engine.inferir_detallado([0.0, 0.0, 0.0], 100.0, 100.0)

    assert result.posterior_sigma == MIN_SIGMA
    assert engine.sigma_p >= MIN_SIGMA


@pytest.mark.parametrize(
    "returns,current,previous",
    [
        ([0.1], 100.0, 99.0),
        ([0.1, float("nan")], 100.0, 99.0),
        ([0.1, float("inf")], 100.0, 99.0),
        ([True, 0.1], 100.0, 99.0),
        ([0.1, 0.2], 0.0, 99.0),
        ([0.1, 0.2], 100.0, -1.0),
        ([0.1, 0.2], float("nan"), 99.0),
        ([0.1, 0.2], 100.0, float("inf")),
    ],
)
def test_invalid_inputs_raise_without_mutating_prior(returns, current, previous):
    engine = ActiveInferenceEngine()
    initial_state = (engine.mu_p, engine.sigma_p)

    with pytest.raises(ValueError):
        engine.inferir(returns, current, previous)

    assert (engine.mu_p, engine.sigma_p) == initial_state


@pytest.mark.parametrize("sigma", [0.0, -0.1, float("nan"), float("inf")])
def test_invalid_prior_sigma_is_rejected(sigma):
    with pytest.raises(ValueError):
        ActiveInferenceEngine(prior_sigma=sigma)


@pytest.mark.parametrize("learning_rate", [0.0, -0.1, 1.1, float("nan")])
def test_invalid_learning_rate_is_rejected(learning_rate):
    with pytest.raises(ValueError):
        ActiveInferenceEngine(learning_rate=learning_rate)


def test_prior_sigma_remains_bounded_after_update():
    engine = ActiveInferenceEngine(prior_sigma=10.0)
    engine.inferir([0.5, -0.5, 0.25], 101.0, 100.0)

    assert MIN_SIGMA <= engine.sigma_p <= 5.0


def test_prior_updates_only_after_successful_inference():
    engine = ActiveInferenceEngine()
    initial_state = (engine.mu_p, engine.sigma_p)

    with pytest.raises(ValueError):
        engine.inferir([0.1, 0.2], 1e308, 1e-308)

    assert (engine.mu_p, engine.sigma_p) == initial_state


def test_kl_is_nonnegative_for_identical_distributions():
    engine = ActiveInferenceEngine(prior_mean=0.0, prior_sigma=0.01)
    result = engine.inferir_detallado([-0.01, 0.01], 100.0, 100.0)

    assert result.kl_divergence >= 0.0
