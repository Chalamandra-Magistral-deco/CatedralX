"""Tests de la Regla Central: 6 dimensiones, 3 estados de salida."""
from REASON.multicriteria import CathedralEvaluation


def test_accepted_when_all_high():
    """Todos los valores altos → ACCEPTED."""
    engine = CathedralEvaluation(0.9, 0.8, 0.7, 0.8, 0.9, 0.9)
    r = engine.evaluate()
    assert r["status"] == "ACCEPTED", f"esperaba ACCEPTED, obtuve {r['status']}"
    assert r["score"] >= 0.75
    assert r["conflicts"] == []


def test_rejected_by_evidence_veto():
    """Evidencia < 0.5 → REJECTED sin importar lo demás."""
    engine = CathedralEvaluation(0.99, 0.8, 0.8, 0.8, 0.9, 0.2)
    r = engine.evaluate()
    assert r["status"] == "REJECTED"
    assert r["reason"] == "EVIDENCIA_INSUFICIENTE"
    assert r["next_action"] == "RECOLECTAR_MAS_DATOS"


def test_uncertain_by_low_resilience():
    """Resiliencia < 0.4 → UNCERTAIN."""
    engine = CathedralEvaluation(0.9, 0.9, 0.9, 0.9, 0.2, 0.9)
    r = engine.evaluate()
    assert r["status"] == "UNCERTAIN"
    assert r["reason"] == "SISTEMA_FRAGIL"


def test_uncertain_by_value_conflict():
    """Alta viabilidad + bajo valor humano → UNCERTAIN."""
    engine = CathedralEvaluation(0.9, 0.1, 0.5, 0.5, 0.8, 0.8)
    r = engine.evaluate()
    assert r["status"] == "UNCERTAIN"
    assert r["reason"] == "CONFLICTO_DE_VALORES"
    assert any("valor humano" in c.lower() for c in r["conflicts"])


def test_rejected_by_low_score():
    """Sin vetos pero score total bajo → REJECTED."""
    engine = CathedralEvaluation(0.4, 0.4, 0.4, 0.4, 0.4, 0.6)
    r = engine.evaluate()
    assert r["status"] == "REJECTED"
    assert r["reason"] == "SCORE_POR_DEBAJO_DEL_UMBRAL"
