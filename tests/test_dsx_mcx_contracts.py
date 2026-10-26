"""Contract tests for DSX (Defense) and MCX (Optimization) gates.
Validates that the system enforces Fail-Closed behavior mathematically.
"""
import pytest
import sys
from pathlib import Path

ELITE_DIR = Path(__file__).resolve().parents[1] / "elite"
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))

from DSX.DEFENSE.guards import cognitive_execution_guard
from REASON.dynamic_constraints import evaluate_dynamic_constraints, DynamicConstraintInputs

class TestDSXDefenseContracts:
    """Valida que el Gate de Defensa DSX funcione como contrato inquebrantable."""
    
    def test_cognitive_execution_guard_allows_coherent_signals(self):
        """Si la disonancia es baja y no hay pánico, el gate debe aprobar."""
        # Inyectamos coherencia explícitamente segura para probar la vía de aprobación
        coherence = {"disonancia": 0.10, "evidence_status": "computed"}
        opposing = {"fuerza_contra": 0.10, "evidence_status": "no_opposing_signal_observed"}
        
        result = cognitive_execution_guard(coherence, opposing, panic=False)
        assert result["allowed"] is True
        assert result["blocked"] is False
        assert len(result["reasons"]) == 0

    def test_cognitive_execution_guard_vetos_on_panic(self):
        """Si hay pánico (panic button), el gate debe vetar sin importar la coherencia."""
        coherence = {"disonancia": 0.10, "evidence_status": "computed"}
        opposing = {"fuerza_contra": 0.10, "evidence_status": "no_opposing_signal_observed"}
        
        result = cognitive_execution_guard(coherence, opposing, panic=True)
        assert result["allowed"] is False
        assert result["blocked"] is True
        assert "panic_active" in result["reasons"]

class TestMCXOptimizationContracts:
    """Valida que las restricciones dinámicas de MCX fallen en modo cerrado (Fail-Closed)."""
    
    def test_dynamic_constraints_fail_closed_on_missing_metrics(self):
        """Si faltan métricas de gobernanza, growth_allowed DEBE ser false."""
        incomplete_inputs = DynamicConstraintInputs(
            reinvestment_surplus=None,
            entropy_rate=None,
            entropy_time_scale=None,
            loop_gain=None,
            signal_count=None,
            optimal_signal_count=None,
            exposure=None,
            max_exposure=None,
            resilience=None,
            minimum_resilience=None
        )
        
        result = evaluate_dynamic_constraints(incomplete_inputs)
        
        assert result["state"] == "RESTRICCIONES_NO_VERIFICADAS"
        assert result["growth_allowed"] is False
        assert "METRICAS_NO_CALIBRADAS" in result["issues"]

    def test_dynamic_constraints_allow_growth_when_valid(self):
        """Si todas las métricas son válidas y cumplen las ecuaciones, el crecimiento se permite."""
        valid_inputs = DynamicConstraintInputs(
            # Ecuación: reinvestment_surplus >= entropy_time_scale * entropy_rate
            # 0.20 >= 10.0 * 0.01 (0.10) -> TRUE
            reinvestment_surplus=0.20,
            entropy_rate=0.01,
            entropy_time_scale=10.0,
            # Ecuación: loop_gain < 1.0 -> 0.8 < 1.0 -> TRUE
            loop_gain=0.8,
            # Ecuación: signal_count <= optimal_signal_count -> 5 <= 5 -> TRUE
            signal_count=5,
            optimal_signal_count=5,
            # Ecuación: exposure <= max_exposure -> 0.1 <= 0.5 -> TRUE
            exposure=0.1,
            max_exposure=0.5,
            # Ecuación: resilience >= minimum_resilience -> 0.9 >= 0.8 -> TRUE
            resilience=0.9,
            minimum_resilience=0.8
        )
        
        result = evaluate_dynamic_constraints(valid_inputs)
        
        assert result["state"] != "RESTRICCIONES_NO_VERIFICADAS"
        assert "MANTENIMIENTO_ENTROPICO" not in result["issues"]
        assert result["growth_allowed"] is True
