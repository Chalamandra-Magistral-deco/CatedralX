import os
"""Falsifiable contracts for the Pergamino's SCX/DSX/FEX/MSX responsibility split."""
from DSX.DEFENSE.guards import cognitive_execution_guard, sustainability_execution_guard
from FEX.FEEDBACK.feedback_loop import resumir_memoria_decisiones
from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad
from MSX.provenance import aggregate_cycle, build_provenance
from REASON.cognitive_state import pairwise_coherence, counterevidence


os.environ.setdefault("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")


def test_scx_coherence_falls_when_signals_disagree():
    agreement = pairwise_coherence([
        {"name": "hurst", "direction": "buy", "confidence": 0.9},
        {"name": "gyro", "direction": "buy", "confidence": 0.9},
    ])
    disagreement = pairwise_coherence([
        {"name": "hurst", "direction": "buy", "confidence": 0.9},
        {"name": "gyro", "direction": "sell", "confidence": 0.9},
    ])
    assert agreement["coherencia"] > 0
    assert disagreement["coherencia"] < 0
    assert disagreement["disonancia"] > agreement["disonancia"]


def test_dsx_blocks_measured_high_dissonance_but_does_not_recalculate_it():
    coherence = {"disonancia": 0.7, "evidence_status": "computed"}
    counter = {"fuerza_contra": 0.1, "evidence_status": "computed"}
    result = cognitive_execution_guard(coherence, counter)
    assert result["blocked"] is True
    assert "high_dissonance" in result["reasons"]
    assert result["enforcement_vector"] == "DSX"


def test_dsx_does_not_block_dissonance_at_exact_threshold():
    result = cognitive_execution_guard(
        {"disonancia": 0.40, "evidence_status": "computed"},
        {"fuerza_contra": 0.1, "evidence_status": "computed"},
    )
    assert result["blocked"] is False


def test_dsx_blocks_nonfinite_cognitive_evidence():
    result = cognitive_execution_guard(
        {"disonancia": float("nan"), "evidence_status": "computed"},
        {"fuerza_contra": 0.1, "evidence_status": "computed"},
    )
    assert result["blocked"] is True
    assert "invalid_dissonance_evidence" in result["reasons"]


def test_dsx_blocks_nonfinite_counterevidence():
    result = cognitive_execution_guard(
        {"disonancia": 0.1, "evidence_status": "computed"},
        {"fuerza_contra": float("inf"), "evidence_status": "computed"},
    )
    assert result["blocked"] is True
    assert "invalid_counterevidence" in result["reasons"]


def test_dsx_blocks_counterevidence_over_threshold():
    result = cognitive_execution_guard(
        {"disonancia": 0.1, "evidence_status": "computed"},
        {"fuerza_contra": 0.8, "evidence_status": "computed"},
    )
    assert result["blocked"] is True
    assert "counterevidence_threshold_exceeded" in result["reasons"]


def test_msx_provenance_contract_and_cycle_aggregation():
    record = build_provenance("hurst", "hurst_analyzer", "v1", {"prices": [1, 2]},
                              output=0.6, confidence=0.7, vector="SCX", parent="cycle-1")
    assert record["vector"] == "SCX"
    assert len(record["input_hash"]) == 64
    assert record["parent"] == "cycle-1"
    assert aggregate_cycle("cycle-1", [record])["record_count"] == 1


def test_msx_rejects_duplicate_provenance_ids():
    record = build_provenance("hurst", "hurst_analyzer", "v1", {"x": 1}, vector="SCX", timestamp=123)
    try:
        aggregate_cycle("cycle-1", [record, record])
    except ValueError as exc:
        assert "duplicado" in str(exc)
    else:
        raise AssertionError("duplicate trace IDs must be rejected")


def test_fex_memory_summary_does_not_invent_outcomes():
    result = resumir_memoria_decisiones(["buy", "buy", "sell", "hold"])
    assert result["ciclos_observados"] == 4
    assert abs(result["sesgo_direccional"] - 1 / 3) < 1e-7
    assert "accuracy" not in result
    assert "pnl" not in result


def test_dsx_blocks_missing_sustainability_report():
    result = sustainability_execution_guard(None)
    assert result["blocked"] is True
    assert result["allowed"] is False
    assert "sustainability_report_missing" in result["reasons"]


def test_dsx_blocks_sustainability_report_when_metrics_are_missing():
    report = {"estado": "CONTINUAR", "crecimiento_permitido": True, "fallos": [],
              "ejecucion_financiera_autorizada": False, "metricas": {"reinvestment_surplus": 1}}
    result = sustainability_execution_guard(report)
    assert result["blocked"] is True
    assert "mandatory_metrics_missing" in result["reasons"]


def test_dsx_blocks_when_sustainability_constraint_fails():
    metrics = {"reinvestment_surplus": 12, "entropy_time_scale": 2, "entropy_rate": 3,
               "loop_gain": 1.0, "signal_count": 4, "optimal_signal_count": 5,
               "exposure": 0.4, "max_exposure": 0.8, "resilience": 0.9,
               "minimum_resilience": 0.6}
    report = evaluar_restricciones_sostenibilidad(**{
        "B": metrics["reinvestment_surplus"], "T": metrics["entropy_time_scale"],
        "dSdt": metrics["entropy_rate"], "G": metrics["loop_gain"],
        "N": metrics["signal_count"], "N_star": metrics["optimal_signal_count"],
        "exposicion": metrics["exposure"], "E_max": metrics["max_exposure"],
        "resiliencia": metrics["resilience"], "R_min": metrics["minimum_resilience"],
    })
    result = sustainability_execution_guard(report)
    assert result["blocked"] is True
    assert "sustainability_constraints_failed" in result["reasons"]


def test_dsx_rejects_sustainability_metrics_mutated_after_fex_evaluation():
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    report["metricas"]["loop_gain"] = 1.0
    result = sustainability_execution_guard(report)
    assert result["blocked"] is True
    assert "sustainability_evidence_integrity_failed" in result["reasons"]


def test_dsx_accepts_complete_sustainability_report_but_never_authorizes_financial_execution():
    metrics = {"reinvestment_surplus": 12, "entropy_time_scale": 2, "entropy_rate": 3,
               "loop_gain": 0.7, "signal_count": 4, "optimal_signal_count": 5,
               "exposure": 0.4, "max_exposure": 0.8, "resilience": 0.9,
               "minimum_resilience": 0.6}
    report = evaluar_restricciones_sostenibilidad(**{
        "B": metrics["reinvestment_surplus"], "T": metrics["entropy_time_scale"],
        "dSdt": metrics["entropy_rate"], "G": metrics["loop_gain"],
        "N": metrics["signal_count"], "N_star": metrics["optimal_signal_count"],
        "exposicion": metrics["exposure"], "E_max": metrics["max_exposure"],
        "resiliencia": metrics["resilience"], "R_min": metrics["minimum_resilience"],
    })
    result = sustainability_execution_guard(report)
    assert result["blocked"] is False
    assert result["allowed"] is True
    assert result["financial_execution_authorized"] is False


def test_dsx_reads_real_panic_marker_in_orchestrator(tmp_path, monkeypatch):
    from DSX.DEFENSE import defense
    from REASON import orchestrator
    from REASON.schemas import SensoryInput

    marker = tmp_path / ".panic"
    marker.write_text("synthetic emergency", encoding="utf-8")
    monkeypatch.setattr(defense, "PATH_PANIC", marker)

    # Use the public cycle path with synthetic observations; emergency must force HOLD.
    prices = [100.0 + i * 0.1 for i in range(40)]
    sensory = SensoryInput(precio_historico=prices, precio_actual=prices[-1])
    state = orchestrator.execute_cycle(sensory, cycle_id="panic-contract-test")
    assert state.decision == "hold"
    assert state.percepcion_espacial["analisis_financiero"]["signal"] == "hold"


def test_cognitive_report_aggregates_msx_trace_for_cycle():
    from REASON.report_composition import build_cognitive_report
    result = build_cognitive_report(
        decision="buy",
        signals=[{"name": "financial_engine", "direction": "buy", "confidence": 0.7}],
        input_evidence={"cycle_id": "trace-cycle-01", "price_count": 30},
    )
    trace = result["provenance"]["cycle_trace"]
    assert trace["cycle_id"] == "trace-cycle-01"
    assert trace["record_count"] == 2
    assert all(record["parent"] == "trace-cycle-01" for record in trace["records"])
