import math

import pytest

from REASON.affective import estado_afectivo, perfil_texto


def test_affective_profile_is_bounded_and_observational():
    result = estado_afectivo({
        "oxitocina_O": 0.8,
        "dopamina_D": 0.75,
        "serotonina_S": 0.9,
        "cortisol_C": 0.1,
        "adrenalina_A": 0.4,
        "melatonina_M": 0.2,
    })

    assert result["estado"] == "CONFIANZA"
    assert 0.0 <= result["activacion"] <= 1.0
    assert -1.0 <= result["valencia"] <= 1.0
    assert -1.0 <= result["calma"] <= 1.0
    assert 0.0 <= result["intensidad"] <= 1.0
    assert result["rol"] == "observacional_no_autoritativo"
    assert result["decision_authority"] is False
    assert result["modelo"] == "heuristico_sintetico_no_calibrado"
    assert "umbral_accion_sugerido" not in result


def test_affective_profile_uses_documented_defaults_for_missing_values():
    result = estado_afectivo({})
    assert result["estado"] == "NEUTRO"
    assert math.isfinite(result["activacion"])
    assert math.isfinite(result["valencia"])
    assert math.isfinite(result["calma"])


@pytest.mark.parametrize(
    "value",
    [True, "0.5", None, float("nan"), float("inf"), -0.01, 1.01],
)
def test_affective_profile_rejects_invalid_concentrations(value):
    with pytest.raises(ValueError):
        estado_afectivo({"cortisol_C": value})


def test_affective_profile_rejects_non_mapping_input():
    with pytest.raises(ValueError, match="diccionario"):
        estado_afectivo([0.1, 0.2])


def test_affective_text_is_descriptive_not_operational():
    text = perfil_texto("CONFIANZA").lower()
    assert "perfil sintético" in text
    assert "operar" not in text
    assert "posición" not in text
    assert "proceder" not in text
