"""Tests for CatedralX's fail-closed integer-basis-point decision rule."""
from decimal import Decimal

import pytest
from REASON.multicriteria import CathedralEvaluation


def test_accepted_when_all_high_and_hash_is_deterministic():
    args = (9000, 9000, 9000, Decimal("0.5"), 9000, 9000)
    first = CathedralEvaluation(*args).evaluate()
    second = CathedralEvaluation(*args).evaluate()
    assert first["status"] == "ACCEPTED", first
    assert first["score"] == 9000
    assert first["score"] >= 7000
    assert first["next_action"] == "SOLICITAR_ACEPTACION_INDEPENDIENTE"
    assert first["evaluation_hash"] == second["evaluation_hash"]
    assert len(first["evaluation_hash"]) == 64
    assert first["dimensions"]["viability"] == 9000


def test_blocked_by_low_evidence():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal("0.5"), 9000, 8499).evaluate()
    assert result["status"] == "BLOCKED_EVIDENCE"
    assert result["reason"] == "EVIDENCIA_INSUFICIENTE"


def test_blocked_by_zero_reinvestment():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal(0), 9000, 9000).evaluate()
    assert result["status"] == "BLOCKED_DEFICIT"
    assert result["reason"] == "SIN_EXCEDENTE_PARA_REINVERSION"


def test_rejected_by_low_integer_score():
    result = CathedralEvaluation(2000, 2000, 2000, Decimal(1), 2000, 9000).evaluate()
    assert result["status"] == "REJECTED"
    assert result["score"] == 2000
    assert result["score"] < 7000


def test_evidence_at_threshold_passes_veto():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal("0.5"), 9000, 8500).evaluate()
    assert result["status"] == "ACCEPTED"
    assert result["reason"] != "EVIDENCIA_INSUFICIENTE"


@pytest.mark.parametrize(
    "bad_value",
    [0.9, 1.5, 10001, -1, float("nan"), float("inf"), True, None, Decimal(9000)],
)
def test_invalid_basis_points_fail_closed(bad_value):
    result = CathedralEvaluation(bad_value, 9000, 9000, Decimal("0.5"), 9000, 9000).evaluate()
    assert result["status"] == "BLOCKED_UNCERTAINTY"
    assert result["reason"] == "ENTRADAS_CUANTITATIVAS_INVALIDAS_O_FALTANTES"
    assert "viability" in result["invalid_inputs"]
    assert result["score"] == 0
    assert len(result["evaluation_hash"]) == 64


def test_invalid_reinvestment_fails_closed():
    for bad_value in (None, True, Decimal("NaN"), float("inf"), "not-money"):
        result = CathedralEvaluation(9000, 9000, 9000, bad_value, 9000, 9000).evaluate()
        assert result["status"] == "BLOCKED_UNCERTAINTY"
        assert "reinvestment" in result["invalid_inputs"]


def test_governance_block_overrides_high_scores_and_is_hashed():
    result = CathedralEvaluation(10000, 10000, 10000, Decimal(100), 10000, 10000).evaluate(
        blocking_reasons=["METRICAS_NO_CALIBRADAS"]
    )
    assert result["status"] == "BLOCKED_UNCERTAINTY"
    assert result["reason"] == "GOBERNANZA_NO_VERIFICADA"
    assert result["blocking_reasons"] == ["METRICAS_NO_CALIBRADAS"]
    assert len(result["evaluation_hash"]) == 64


def test_integer_inputs_are_basis_points_and_hash_includes_policy_result():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal(100), 9000, 8500).evaluate()
    assert result["dimensions"]["evidence"] == 8500
    assert result["dimensions"]["reinvestment"] == "100"
    assert result["score"] == 9000
    other = CathedralEvaluation(9000, 9000, 9000, Decimal(100), 9000, 9001).evaluate()
    assert result["evaluation_hash"] != other["evaluation_hash"]
