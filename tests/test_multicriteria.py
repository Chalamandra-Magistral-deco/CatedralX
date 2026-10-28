"""Tests for CatedralX's sealed deterministic basis-point decision rule."""
from decimal import Decimal

from REASON.multicriteria import CathedralEvaluation


def test_accepted_when_all_high_and_hash_is_deterministic():
    args = (Decimal("0.9"), Decimal("0.9"), Decimal("0.9"), Decimal("0.5"), Decimal("0.9"), Decimal("0.9"))
    first = CathedralEvaluation(*args).evaluate()
    second = CathedralEvaluation(*args).evaluate()
    assert first["status"] == "ACCEPTED", first
    assert first["score"] == 9000
    assert first["score"] >= 7000
    assert first["evaluation_hash"] == second["evaluation_hash"]
    assert len(first["evaluation_hash"]) == 64
    assert first["dimensions"]["viability"] == 9000


def test_blocked_by_low_evidence():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal("0.5"), 9000, Decimal("0.5")).evaluate()
    assert result["status"] == "BLOCKED_EVIDENCE"
    assert result["reason"] == "EVIDENCIA_INSUFICIENTE"


def test_blocked_by_zero_reinvestment():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal("0.0"), 9000, 9000).evaluate()
    assert result["status"] == "BLOCKED_REINVERSION"
    assert result["reason"] == "SIN_EXCEDENTE_PARA_REINVERSION"


def test_rejected_by_low_integer_score():
    result = CathedralEvaluation(2000, 2000, 2000, 500, 2000, 9000).evaluate()
    assert result["status"] == "REJECTED"
    assert result["score"] == 2000
    assert result["score"] < 7000


def test_evidence_at_threshold_passes_veto():
    result = CathedralEvaluation(9000, 9000, 9000, Decimal("0.5"), 9000, 8500).evaluate()
    assert result["status"] == "ACCEPTED"
    assert result["reason"] != "EVIDENCIA_INSUFICIENTE"


def test_nonfinite_input_is_sanitized_without_nan_output():
    result = CathedralEvaluation(float("nan"), 9000, 9000, Decimal("0.5"), 9000, 9000).evaluate()
    assert result["status"] == "REJECTED"
    assert result["dimensions"]["viability"] == 0
    assert result["evaluation_hash"]


def test_integer_inputs_are_basis_points_and_hash_includes_policy_result():
    result = CathedralEvaluation(9000, 9000, 9000, 100, 9000, 8500).evaluate()
    assert result["dimensions"]["evidence"] == 8500
    assert result["dimensions"]["reinvestment"] == "100"
    assert result["score"] == 9000
    assert result["evaluation_hash"] != CathedralEvaluation(9000, 9000, 9000, 100, 9000, 9001).evaluate()["evaluation_hash"]
