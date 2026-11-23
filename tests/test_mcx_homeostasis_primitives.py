from elite.MCX.OPTIMIZE.homeostasis import tamaño_posicion_optimo


def test_position_sizing_returns_zero_without_observations():
    assert tamaño_posicion_optimo([]) == 0.0


def test_position_sizing_allows_zero_exposure_for_negative_returns():
    assert tamaño_posicion_optimo([-0.02, -0.05, -0.01]) == 0.0


def test_position_sizing_can_select_positive_exposure_when_growth_improves():
    assert tamaño_posicion_optimo([0.04, 0.05, 0.03]) > 0.0
