"""Hard governance gates for the dynamic Cathedral loop."""

import math

from REASON.dynamic_constraints import (
    DynamicConstraintInputs,
    evaluate_dynamic_constraints,
)


def _safe_inputs():
    return DynamicConstraintInputs(
        reinvestment_surplus=10.0,
        entropy_rate=1.0,
        entropy_time_scale=2.0,
        loop_gain=0.7,
        dominant_signal_weight=0.4,
        minimum_confidence=0.8,
        signal_count=4,
        optimal_signal_count=5,
        exposure=0.2,
        max_exposure=0.5,
        resilience=0.9,
        minimum_resilience=0.7,
        degradation_rate=0.01,
        accumulated_noise=0.02,
    )


def test_all_hard_constraints_must_pass_before_growth():
    result = evaluate_dynamic_constraints(_safe_inputs())
    assert result["state"] == "CRECIMIENTO_PERMITIDO"
    assert result["growth_allowed"] is True
    assert result["automatic_recalibration"] is False
    assert result["automatic_modularization"] is False


def test_entropy_shortfall_enters_maintenance():
    inputs = _safe_inputs()
    inputs = DynamicConstraintInputs(**{**inputs.__dict__, "reinvestment_surplus": 1.0})
    result = evaluate_dynamic_constraints(inputs)
    assert result["state"] == "MANTENIMIENTO"
    assert result["growth_allowed"] is False
    assert "MANTENIMIENTO_ENTROPICO" in result["issues"]


def test_loop_gain_at_or_above_one_activates_dynamic_brake():
    inputs = DynamicConstraintInputs(**{**_safe_inputs().__dict__, "loop_gain": 1.0})
    result = evaluate_dynamic_constraints(inputs)
    assert result["state"] == "FRENO_DINAMICO"
    assert result["growth_allowed"] is False
    assert "FRENO_DINAMICO" in result["issues"]


def test_scale_breach_requires_modularization_or_lower_exposure():
    inputs = DynamicConstraintInputs(**{**_safe_inputs().__dict__, "signal_count": 6})
    result = evaluate_dynamic_constraints(inputs)
    assert result["state"] == "MODULARIZAR"
    assert result["growth_allowed"] is False


def test_signal_counts_must_be_nonnegative_integers():
    for field, value in (
        ("signal_count", 2.9),
        ("signal_count", 2.0),
        ("signal_count", -1),
        ("signal_count", True),
        ("optimal_signal_count", 2.9),
        ("optimal_signal_count", 2.0),
        ("optimal_signal_count", -1),
        ("optimal_signal_count", False),
    ):
        inputs = DynamicConstraintInputs(**{**_safe_inputs().__dict__, field: value})
        result = evaluate_dynamic_constraints(inputs)
        assert result["growth_allowed"] is False, (field, value)
        assert "DATOS_INVALIDOS" in result["issues"], (field, value)
        assert field in result["invalid_metrics"], (field, value)


def test_negative_or_out_of_domain_metrics_never_authorize_growth():
    invalid_values = (
        ("reinvestment_surplus", -0.01),
        ("entropy_rate", -0.01),
        ("entropy_time_scale", 0.0),
        ("entropy_time_scale", -0.01),
        ("loop_gain", -0.01),
        ("exposure", -0.01),
        ("max_exposure", -0.01),
        ("resilience", -0.01),
        ("resilience", 1.01),
        ("minimum_resilience", -0.01),
        ("minimum_resilience", 1.01),
        ("dominant_signal_weight", 1.01),
        ("minimum_confidence", 1.01),
        ("degradation_rate", -0.01),
        ("accumulated_noise", -0.01),
    )
    for field, value in invalid_values:
        inputs = DynamicConstraintInputs(**{**_safe_inputs().__dict__, field: value})
        result = evaluate_dynamic_constraints(inputs)
        assert result["growth_allowed"] is False, (field, value)
        assert "DATOS_INVALIDOS" in result["issues"], (field, value)
        assert field in result["invalid_metrics"], (field, value)


def test_missing_or_nonfinite_metrics_never_authorize_growth():
    missing = evaluate_dynamic_constraints(DynamicConstraintInputs())
    assert missing["growth_allowed"] is False
    assert "METRICAS_NO_CALIBRADAS" in missing["issues"]

    invalid = DynamicConstraintInputs(**{**_safe_inputs().__dict__, "loop_gain": math.nan})
    result = evaluate_dynamic_constraints(invalid)
    assert result["growth_allowed"] is False
    assert "DATOS_INVALIDOS" in result["issues"]


def test_orchestrator_holds_directional_signal_on_measured_hard_breach(tmp_path):
    import math

    from REASON import orchestrator
    from REASON.schemas import SensoryInput

    orchestrator._think_orchestrator.transductor.output_path = tmp_path / "state.json"
    prices = [100.0 * math.exp(0.001 * index) for index in range(60)]
    constraints = {
        "reinvestment_surplus": 1.0,
        "entropy_rate": 1.0,
        "entropy_time_scale": 2.0,
        "loop_gain": 0.7,
        "dominant_signal_weight": 0.4,
        "minimum_confidence": 0.8,
        "signal_count": 4,
        "optimal_signal_count": 5,
        "exposure": 0.2,
        "max_exposure": 0.5,
        "resilience": 0.9,
        "minimum_resilience": 0.7,
        "degradation_rate": 0.01,
        "accumulated_noise": 0.02,
    }
    state = orchestrator.execute_cycle(SensoryInput(
        precio_historico=prices, precio_actual=prices[-1], dynamic_constraints=constraints
    ))
    assert state.decision == "hold"
    assert state.percepcion_espacial["dynamic_constraints"]["state"] == "MANTENIMIENTO"
    assert state.percepcion_espacial["growth_allowed"] is False
    assert state.percepcion_espacial["analisis_financiero"]["trading_enabled"] is False



def test_orchestrator_does_not_infer_viability_from_market_direction(tmp_path):
    from REASON import orchestrator
    from REASON.schemas import SensoryInput

    orchestrator._think_orchestrator.transductor.output_path = tmp_path / "state.json"
    prices = [100.0 * math.exp(0.001 * index) for index in range(60)]
    constraints = _safe_inputs().__dict__
    dimensions = {
        "human_value_bp": 9000,
        "distribution_bp": 9000,
        "resilience_bp": 9000,
        "evidence_bp": 9000,
    }
    state = orchestrator.execute_cycle(SensoryInput(
        precio_historico=prices,
        precio_actual=prices[-1],
        dynamic_constraints=constraints,
        central_dimensions_bp=dimensions,
    ), cycle_id="missing-explicit-viability")

    verdict = state.cognicion["cathedral_verdict"]
    assert verdict["status"] == "BLOCKED_UNCERTAINTY"
    assert "viability" in verdict["invalid_inputs"]
    assert verdict["score"] == 0


def test_central_dimensions_reject_noncanonical_reinvestment_field():
    from PERCEIVE.percepcion import validar_campos_gobernanza

    with pytest.raises(ValueError, match="claves no canónicas"):
        validar_campos_gobernanza({
            "CENTRAL_DIMENSIONS_BP": {
                "viability_bp": 9000,
                "reinvestment_surplus": "100.00",
            }
        })


def test_snapshot_carries_central_dimensions_into_central_rule_without_inference(tmp_path):
    from REASON import orchestrator

    orchestrator._think_orchestrator.transductor.output_path = tmp_path / "state.json"
    prices = [100.0 * math.exp(0.001 * index) for index in range(60)]
    dimensions = {
        "viability_bp": 7800,
        "human_value_bp": 8100,
        "distribution_bp": 7600,
        "resilience_bp": 9000,
        "evidence_bp": 9200,
    }
    constraints = {
        "reinvestment_surplus": 125.5,
        "entropy_rate": 0.1,
        "entropy_time_scale": 2.0,
        "loop_gain": 0.7,
        "signal_count": 3,
        "optimal_signal_count": 5,
        "exposure": 0.2,
        "max_exposure": 0.5,
        "resilience": 0.9,
        "minimum_resilience": 0.7,
    }
    snapshot = {
        "PERCEIVE": {
            "historial_precios": prices,
            "precio": prices[-1],
            "gap": 0.0,
            "inercia": 0.0,
        },
        "CENTRAL_DIMENSIONS_BP": dimensions,
        "DYNAMIC_CONSTRAINTS": constraints,
    }
    sensory = orchestrator._think_orchestrator._construir_sensory_input(snapshot)
    assert sensory.central_dimensions_bp == dimensions
    assert sensory.dynamic_constraints == constraints
    state = orchestrator.execute_cycle(sensory, cycle_id="governance-transport-test")
    assert state.percepcion_espacial["central_dimensions_bp"] == dimensions
    assert state.percepcion_espacial["dynamic_constraints_input"] == constraints
    # The dimensions are carried to the rule, but viability and other policy gates
    # remain independently evaluated; no transport field itself grants acceptance.
    assert state.cognicion["cathedral_verdict"]["dimensions"]["viability"] == 7800
    assert state.cognicion["cathedral_verdict"]["dimensions"]["human_value"] == 8100
    assert state.cognicion["cathedral_verdict"]["dimensions"]["distribution"] == 7600
    assert state.cognicion["cathedral_verdict"]["dimensions"]["reinvestment"] == "125.5"


def test_from_snapshot_preserves_governance_contracts():
    from PERCEIVE.percepcion import from_snapshot

    dimensions = {"human_value_bp": 9000}
    constraints = {"signal_count": 3, "optimal_signal_count": 5}
    snapshot = {
        "PERCEIVE": {
            "historial_precios": [100.0 + index for index in range(30)],
            "precio": 129.0,
        },
        "CENTRAL_DIMENSIONS_BP": dimensions,
        "DYNAMIC_CONSTRAINTS": constraints,
    }

    sensory = from_snapshot(snapshot)
    assert sensory.central_dimensions_bp == dimensions
    assert sensory.dynamic_constraints == constraints


def test_from_snapshot_rejects_non_object_governance_contracts():
    from PERCEIVE.percepcion import from_snapshot

    base = {
        "PERCEIVE": {
            "historial_precios": [100.0 + index for index in range(30)],
            "precio": 129.0,
        }
    }
    for key in ("DYNAMIC_CONSTRAINTS", "CENTRAL_DIMENSIONS_BP"):
        invalid = {**base, key: [1, 2, 3]}
        try:
            from_snapshot(invalid)
        except ValueError as exc:
            assert "debe ser un objeto" in str(exc)
        else:
            raise AssertionError(f"{key} must reject non-object values")


def test_snapshot_rejects_non_object_governance_contracts():
    from REASON import orchestrator

    prices = [100.0 + index for index in range(30)]
    base = {"PERCEIVE": {"historial_precios": prices, "precio": prices[-1]}}
    for key in ("DYNAMIC_CONSTRAINTS", "CENTRAL_DIMENSIONS_BP"):
        invalid = {**base, key: [1, 2, 3]}
        try:
            orchestrator._think_orchestrator._construir_sensory_input(invalid)
        except ValueError as exc:
            assert "debe ser un objeto" in str(exc)
        else:
            raise AssertionError(f"{key} must reject non-object values")


def test_orchestrator_cannot_accept_when_dynamic_constraints_are_missing(tmp_path):
    from REASON import orchestrator
    from REASON.schemas import SensoryInput

    orchestrator._think_orchestrator.transductor.output_path = tmp_path / "state.json"
    prices = [100.0 * math.exp(0.001 * index) for index in range(60)]
    state = orchestrator.execute_cycle(SensoryInput(
        precio_historico=prices,
        precio_actual=prices[-1],
        dynamic_constraints={},
    ), cycle_id="p0-empty-governance-regression")

    report = state.percepcion_espacial["dynamic_constraints"]
    verdict = state.cognicion["cathedral_verdict"]
    assert report["growth_allowed"] is False
    assert "METRICAS_NO_CALIBRADAS" in report["issues"]
    assert verdict["status"] == "BLOCKED_UNCERTAINTY"
    assert verdict["status"] != "ACCEPTED"
    assert verdict["reason"] == "GOBERNANZA_NO_VERIFICADA"
