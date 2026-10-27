"""Tests de la Regla Central (spec sellada en DECISIONS.md, Fase 1)."""
from REASON.multicriteria import CathedralEvaluation


def test_accepted_when_all_high():
    e = CathedralEvaluation(0.9, 0.9, 0.9, 0.5, 0.9, 0.9)
    r = e.evaluate()
    assert r["status"] == "ACCEPTED", r
    assert r["score"] >= 0.70


def test_blocked_by_low_evidence():
    e = CathedralEvaluation(0.9, 0.9, 0.9, 0.5, 0.9, 0.5)
    r = e.evaluate()
    assert r["status"] == "BLOCKED_UNCERTAINTY"
    assert r["reason"] == "EVIDENCIA_INSUFICIENTE"


def test_blocked_by_zero_reinvestment():
    e = CathedralEvaluation(0.9, 0.9, 0.9, 0.0, 0.9, 0.9)
    r = e.evaluate()
    assert r["status"] == "BLOCKED_DEFICIT"
    assert r["reason"] == "SIN_EXCEDENTE_PARA_REINVERSION"


def test_rejected_by_low_score():
    e = CathedralEvaluation(0.2, 0.2, 0.2, 0.5, 0.2, 0.9)
    r = e.evaluate()
    assert r["status"] == "REJECTED"
    assert r["reason"] == "BAJO_RENDIMIENTO_GLOBAL"


def test_evidence_at_threshold_passes_veto():
    e = CathedralEvaluation(0.9, 0.9, 0.9, 0.5, 0.9, 0.85)
    r = e.evaluate()
    assert r["status"] in ("ACCEPTED", "REJECTED"), r
    assert r["reason"] != "EVIDENCIA_INSUFICIENTE"


def test_nan_inputs_are_sanitized():
    e = CathedralEvaluation(float("nan"), 0.9, 0.9, 0.5, 0.9, 0.9)
    r = e.evaluate()
    # NaN en viability se sanitiza a 0.0; con los pesos, score < 0.70 → REJECTED
    assert r["status"] in ("REJECTED", "BLOCKED_UNCERTAINTY", "BLOCKED_DEFICIT"), r
