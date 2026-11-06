import math

from elite.FEX.FEEDBACK.feedback_loop import resumir_memoria_decisiones
from elite.MSX.provenance import build_provenance
from elite.REASON.cognitive_state import (
    counterevidence,
    metacognition,
    pairwise_coherence,
    regime_context,
    uncertainty,
)
from elite.REASON.report_composition import build_cognitive_report


def test_opposing_signals_report_dissonance_without_enforcing_block():
    result = pairwise_coherence([
        {"name": "a", "direction": "buy", "confidence": 0.9},
        {"name": "b", "direction": "sell", "confidence": 0.8},
    ])
    assert result["coherencia"] == -0.72
    assert result["disonancia"] == 0.86
    assert result["dissonance_threshold_exceeded"] is True
    assert "hard_block" not in result


def test_high_dissonance_is_reported_for_dsx_enforcement():
    result = pairwise_coherence([
        {"name": "a", "direction": "buy", "confidence": 1.0},
        {"name": "b", "direction": "sell", "confidence": 1.0},
    ])
    assert result["disonancia"] == 1.0
    assert result["coherencia"] == -1.0
    assert result["dissonance_threshold_exceeded"] is True
    assert "hard_block" not in result


def test_missing_confidence_is_not_inferred():
    result = pairwise_coherence([{"name": "a", "direction": "buy"}, {"name": "b", "direction": "sell", "confidence": 0.7}])
    assert result["evidence_status"] == "insufficient_evidence"
    assert result["senales_excluidas"] == ["a"]


def test_neutral_direction_has_zero_pair_agreement():
    result = pairwise_coherence([
        {"name": "a", "direction": "hold", "confidence": 0.9},
        {"name": "b", "direction": "buy", "confidence": 0.9},
    ])
    assert result["coherencia"] is None
    assert result["evidence_status"] == "insufficient_evidence"


def test_counterevidence_blocks_when_weighted_opposition_exceeds_threshold():
    result = counterevidence("buy", [
        {"name": "opposing", "direction": "sell", "confidence": 0.9, "weight": 0.8}
    ], abort_threshold=0.35)
    assert result["fuerza_contra"] == 0.9
    assert result["decision_sobrevive"] is False


def test_uncertainty_requires_both_components():
    assert uncertainty(3.0, 4.0)["u_total"] == 5.0
    assert uncertainty(3.0, None)["u_total"] is None


def test_metacognition_marks_calibration_gap_not_brier_or_ece():
    c = {"disonancia": 0.1}
    result = metacognition(coherence=c, confidence=0.8, historical_accuracy=0.6, error_slope=0.0)
    assert math.isclose(result["brecha_calibracion"], 0.2)
    assert result["needs_review"] is True
    assert result["calibration_status"] == "diagnostic_gap_only_not_brier_or_ece"


def test_metacognition_does_not_invent_uncertainty():
    result = metacognition(coherence={"disonancia": None})
    assert result["incertidumbre"] is None
    assert result["riesgo_caos"] is None


def test_markov_context_uses_laplace_smoothing_and_observed_labels():
    result = regime_context(["LATERAL", "LATERAL", "TREND", "TREND"])
    assert result["fase_actual"] == "TREND"
    assert result["fase_anterior"] == "TREND"
    assert result["tiempo_en_regimen"] == 2
    assert 0 <= result["P_salida"] <= 1
    assert result["evidence_status"] == "computed_from_observed_labels"


def test_markov_context_handles_insufficient_history():
    result = regime_context(["TREND"])
    assert result["P_salida"] is None
    assert result["evidence_status"] == "insufficient_regime_history"


def test_decision_memory_computes_directional_bias_without_pnl_claims():
    result = resumir_memoria_decisiones(["buy", "buy", "sell", "hold"])
    assert math.isclose(result["sesgo_direccional"], 1 / 3, abs_tol=1e-7)
    assert result["ciclos_observados"] == 4
    assert "precision" not in result


def test_provenance_has_sha256_and_does_not_fake_confidence():
    result = build_provenance("x", "module", "v1", {"a": 1}, confidence=None)
    assert len(result["input_hash_sha256"]) == 64
    assert result["confidence"] is None
    assert result["confidence_status"] == "unavailable"


def test_integrated_report_keeps_trading_disabled_and_unknowns_explicit():
    result = build_cognitive_report(decision="buy", signals=[{"name": "legacy", "direction": "buy"}], input_evidence={"price": 1})
    assert result["operational_policy"]["trading_enabled"] is False
    assert result["coherencia"]["evidence_status"] == "insufficient_evidence"
    assert result["metacognicion"]["incertidumbre"] is None
    assert result["provenance"]["cognitive_report"]["input_hash_sha256"]
