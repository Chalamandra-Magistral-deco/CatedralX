import math

import pytest

from elite.REASON.anharmonic import analyze


def test_preserves_two_float_api_and_expected_values():
    cross_ratio, score = analyze([1.0, 2.0, 3.0, 4.0])
    assert isinstance(cross_ratio, float)
    assert isinstance(score, float)
    assert cross_ratio == pytest.approx(0.75)
    assert score == pytest.approx(1.0)


def test_uses_only_last_four_observations():
    assert analyze([100.0, 1.0, 2.0, 3.0, 4.0]) == analyze([1.0, 2.0, 3.0, 4.0])


def test_short_series_keeps_legacy_neutral_result():
    assert analyze([10.0, 11.0, 12.0]) == (0.0, 0.0)


@pytest.mark.parametrize("prices", [
    [1.0, 2.0, 3.0, float("nan")],
    [1.0, 2.0, 3.0, float("inf")],
    [1.0, 2.0, 3.0, -float("inf")],
    [1.0, 2.0, 3.0, 0.0],
    [1.0, 2.0, 3.0, -1.0],
    [1.0, 2.0, 3.0, True],
    [1.0, 2.0, 3.0, "4.0"],
    [1.0, 2.0, 3.0, None],
])
def test_rejects_invalid_prices(prices):
    with pytest.raises(ValueError):
        analyze(prices)


def test_rejects_non_list_or_tuple_input():
    with pytest.raises(TypeError):
        analyze(None)


def test_degenerate_denominator_returns_neutral_result():
    assert analyze([1.0, 2.0, 3.0, 1.0]) == (0.0, 0.0)


def test_large_finite_prices_do_not_overflow_dispersion_mean():
    cross_ratio, score = analyze([8e307, 9e307, 1e308, 7e307])
    assert math.isfinite(cross_ratio)
    assert math.isfinite(score)
    assert 0.0 <= score <= 1.0


def test_score_is_bounded():
    _, score = analyze([100.0, 101.0, 102.0, 103.0])
    assert 0.0 <= score <= 1.0
