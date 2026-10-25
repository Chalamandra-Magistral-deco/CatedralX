"""Isolated acceptance checks for CatedralX critical safety contracts.

Uses synthetic observations and tmp_path only. No market APIs, order execution,
or writes to the user's original working tree/state paths.
"""
from __future__ import annotations

import os

import json
from datetime import datetime, timedelta, timezone

import pytest

from PERCEIVE.api_pulse import validate_snapshot_payload
from FEX.FEEDBACK.feedback_loop import (
    evaluar_feedback,
    registrar_prediccion,
    registrar_resultado,
)


os.environ.setdefault("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")


def observation(*, observed_at: str | None = None, prices=None):
    values = list(prices if prices is not None else [100.0 + i * 0.1 for i in range(30)])
    return {
        "PERCEIVE": {
            "historial_precios": values,
            "precio": values[-1] if values else None,
            "source": "synthetic_acceptance_test:ASSET:1m",
            "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        }
    }


def synthetic_prediction():
    return {
        "decision": "hold",
        "signal_strength": 0.25,
        "signal_strength_is_probability": False,
        "regime": "SYNTHETIC_TEST",
        "reference_price": 102.9,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "market_source": "synthetic_acceptance_test:ASSET:1m",
        "trading_enabled": False,
        "orders_created": False,
        "orders_executed": False,
    }


def test_acceptance_valid_synthetic_observation_is_accepted():
    result = validate_snapshot_payload(observation(), max_age_seconds=120)
    assert result["healthy"] is True
    assert result["reason"] == "ok"
    assert result["has_prices"] is True


@pytest.mark.parametrize(
    ("payload", "expected_reason"),
    [
        (None, "invalid_snapshot_schema"),
        ({}, "missing_perceive_section"),
        (observation(prices=[100.0] * 29), "insufficient_price_history"),
        (observation(prices=[100.0] * 29 + [0.0]), "invalid_price_history"),
    ],
)
def test_acceptance_invalid_observations_fail_closed(payload, expected_reason):
    result = validate_snapshot_payload(payload, max_age_seconds=120)
    assert result["healthy"] is False
    assert result["reason"] == expected_reason


def test_acceptance_feedback_requires_known_prediction_and_valid_horizon(tmp_path):
    ledger = tmp_path / "acceptance-feedback.jsonl"
    with pytest.raises(ValueError, match="no existe"):
        registrar_resultado(
            "missing-synthetic-id",
            {
                "horizon": "1m",
                "observed_price": 103.0,
                "observed_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
                "source": "synthetic_acceptance_test:ASSET:1m",
            },
            ledger,
        )

    prediction_id = registrar_prediccion(
        synthetic_prediction(), ledger, prediction_id="acceptance-synthetic-001"
    )
    with pytest.raises(ValueError, match="Horizonte aún no vencido"):
        registrar_resultado(
            prediction_id,
            {
                "horizon": "1m",
                "observed_price": 103.0,
                "observed_at": (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat(),
                "source": "synthetic_acceptance_test:ASSET:1m",
            },
            ledger,
        )


def test_acceptance_feedback_report_keeps_trading_and_retraining_disabled(tmp_path):
    ledger = tmp_path / "acceptance-feedback.jsonl"
    registrar_prediccion(synthetic_prediction(), ledger, prediction_id="acceptance-synthetic-002")
    report = evaluar_feedback(ledger)

    assert report["predictions_recorded"] == 1
    assert report["predictions_pending_outcome"] == 1
    assert report["trading_enabled"] is False
    assert report["automatic_retraining"] is False
    assert all(
        row.get("orders_created") is False and row.get("orders_executed") is False
        for row in [json.loads(line)["prediction"] for line in ledger.read_text().splitlines()]
    )


def test_acceptance_rejects_stale_and_timezone_naive_observations():
    now = datetime.now(timezone.utc)
    stale = observation(observed_at=(now - timedelta(minutes=10)).isoformat())
    stale_result = validate_snapshot_payload(stale, max_age_seconds=120, now=now.timestamp())
    assert stale_result["healthy"] is False
    assert stale_result["reason"] == "stale_observation"

    naive = observation(observed_at=now.replace(tzinfo=None).isoformat())
    naive_result = validate_snapshot_payload(naive, max_age_seconds=120, now=now.timestamp())
    assert naive_result["healthy"] is False
    assert naive_result["reason"] == "observed_at_requires_timezone"


def test_acceptance_one_shot_entrypoint_never_executes_stale_snapshot(tmp_path, monkeypatch):
    from REASON import razon

    snapshot_path = tmp_path / "stale-snapshot.json"
    snapshot_path.write_text(
        json.dumps(observation(observed_at=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat())),
        encoding="utf-8",
    )
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setattr(
        razon,
        "execute_cycle",
        lambda *_args, **_kwargs: pytest.fail("execute_cycle must not run on stale data"),
    )

    assert razon.main() == 2


def test_acceptance_bunker_entrypoint_never_executes_stale_snapshot(tmp_path, monkeypatch):
    from PERCEIVE import bunker

    snapshot_path = tmp_path / "stale-snapshot.json"
    snapshot_path.write_text(
        json.dumps(observation(observed_at=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat())),
        encoding="utf-8",
    )
    monkeypatch.setattr(bunker, "SNAPSHOT_PATH", snapshot_path)
    monkeypatch.setattr(
        bunker,
        "execute_cycle",
        lambda *_args, **_kwargs: pytest.fail("execute_cycle must not run on stale data"),
    )

    with pytest.raises(ValueError, match="Snapshot rechazado: stale_observation"):
        bunker.BunkerDaemon()._ciclo()


def test_acceptance_synthetic_scx_fex_dsx_aex_stub_cycle(monkeypatch):
    """Exercise the vector contract end-to-end without calling the order writer."""
    import numpy as np
    from DSX.DEFENSE.guards import final_execution_guard
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad
    from REASON.report_composition import build_cognitive_report

    monkeypatch.setenv("CATEDRALX_DSX_AUTH_SECRET", "test-only-dsx-secret-material-32-bytes")
    cycle_id = "synthetic-cycle-acceptance-01"
    decision = {"accion": "ENTRAR_LARGO", "tamano": 0.1, "confianza": 0.8,
                "razon": "synthetic-only; no market intent"}

    # SCX: independently computed diagnostics; DSX consumes, does not recalculate.
    scx = build_cognitive_report(
        decision="buy",
        signals=[
            {"name": "synthetic_financial", "direction": "buy", "confidence": 0.8},
            {"name": "synthetic_gyro", "direction": "buy", "confidence": 0.7},
        ],
        input_evidence={"cycle_id": cycle_id, "synthetic": True, "trading_enabled": False},
    )
    assert scx["provenance"]["cycle_trace"]["cycle_id"] == cycle_id

    # FEX: governance report is computed from synthetic constraints and hashed.
    fex = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    assert fex["ejecucion_financiera_autorizada"] is False

    # DSX: signs an exact-intent authorization; it still cannot authorize finance.
    dsx = final_execution_guard(
        scx["coherencia"], scx["contraevidencia"], fex,
        decision_context=decision, reference_price=100.0,
    )
    assert dsx["allowed"] is True
    assert dsx["blocked"] is False
    assert dsx["dsx_signature"]
    assert dsx["financial_execution_authorized"] is False

    # AEX is a stub: record a proposed hand-off, never invoke order creation/execution.
    calls = []
    def aex_stub(*, authorization, intent, reference_price):
        calls.append((authorization, intent, reference_price))
        return {"stub": True, "orders_created": False, "orders_executed": False}

    outcome = aex_stub(authorization=dsx, intent=decision, reference_price=100.0)
    assert outcome["stub"] is True
    assert outcome["orders_created"] is False
    assert outcome["orders_executed"] is False
    assert len(calls) == 1


def test_acceptance_dsx_rejects_missing_disconnected_and_tampered_fex_report():
    from DSX.DEFENSE.guards import sustainability_execution_guard
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad

    assert sustainability_execution_guard(None)["blocked"] is True
    disconnected = {"estado": "CONTINUAR", "fallos": [], "crecimiento_permitido": True,
                    "ejecucion_financiera_autorizada": False, "metricas": {}}
    disconnected_result = sustainability_execution_guard(disconnected)
    assert disconnected_result["blocked"] is True
    assert "sustainability_evidence_integrity_failed" in disconnected_result["reasons"]

    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    report["metricas"]["loop_gain"] = 0.1  # mutate after FEX produced its evidence hash
    tampered_result = sustainability_execution_guard(report)
    assert tampered_result["blocked"] is True
    assert "sustainability_evidence_integrity_failed" in tampered_result["reasons"]


def test_acceptance_duplicate_trainers_have_equivalent_math_but_different_api_names():
    import numpy as np
    from FEX.FEEDBACK import trainer as feedback_trainer
    from FEX import trainer as root_trainer

    weights = np.asarray([0.2, -0.1, 0.05], dtype=float)
    inputs = [0.3, 0.8]
    target = 1.0
    root_weights, root_loss = root_trainer.entrenar_paso(inputs, target, weights.copy(), tasa=0.02)
    feedback_weights, feedback_loss = feedback_trainer.actualizar_modelo(inputs, target, weights.copy(), tasa=0.02)
    np.testing.assert_allclose(root_weights, feedback_weights, rtol=0, atol=1e-12)
    assert root_loss == pytest.approx(feedback_loss, abs=1e-12)
    np.testing.assert_allclose(
        root_trainer.sgd_paso(weights, np.ones_like(weights), 0.01),
        feedback_trainer.sgd_step(weights, np.ones_like(weights), 0.01),
        rtol=0, atol=1e-12,
    )


def test_acceptance_fex_rejects_forged_report_even_if_hash_is_recomputed(monkeypatch):
    from DSX.DEFENSE.guards import sustainability_execution_guard
    from FEX.GOVERNANCE.sustainability import (
        evaluar_restricciones_sostenibilidad,
        hash_evidencia_sostenibilidad,
    )

    monkeypatch.setenv("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    # Simulate a hostile caller: modify FEX metrics and recalculate the public hash,
    # but the caller cannot create the HMAC signature for the new content.
    report["metricas"]["loop_gain"] = 0.2
    report["evidence_hash"] = hash_evidencia_sostenibilidad(report)
    result = sustainability_execution_guard(report)
    assert result["blocked"] is True
    assert "sustainability_evidence_integrity_failed" in result["reasons"]


def test_acceptance_fex_report_fails_closed_when_authentication_secret_missing(monkeypatch):
    from DSX.DEFENSE.guards import sustainability_execution_guard
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad

    monkeypatch.delenv("CATEDRALX_FEX_EVIDENCE_SECRET", raising=False)
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    assert report["evidence_signature"] is None
    result = sustainability_execution_guard(report)
    assert result["blocked"] is True
    assert "sustainability_evidence_integrity_failed" in result["reasons"]



def _run_real_orchestrator_cycle(monkeypatch, tmp_path, *, provider=None, panic=False, dynamic_constraints=None):
    import REASON.orchestrator as orchestrator_module
    from DSX.DEFENSE import defense
    from REASON.schemas import SensoryInput

    class MemoryOnlyTransductor:
        def __init__(self, output_path=None):
            self.package = {}
        def volcar_estado_quimico(self, package):
            self.package = package
        def leer_estado_actual(self):
            return {"concentracion_actual": {}}

    monkeypatch.setattr(orchestrator_module, "TransductorEndocrino", MemoryOnlyTransductor)
    monkeypatch.setattr(orchestrator_module, "analyze_financial_market", lambda _prices: {
        "signal": "buy", "signal_strength": 0.7, "risk_flags": [],
        "regime": "SYNTHETIC_TEST", "combined_signal": "compra",
        "decision_reason": "synthetic-only", 
    })
    monkeypatch.setattr(orchestrator_module, "build_cognitive_report", lambda **_kwargs: {
        "coherencia": {"disonancia": 0.1},
        "contraevidencia": {"fuerza_contra": 0.1, "evidence_status": "computed"},
        "operational_policy": {}, "contexto": {}, "decision": "buy",
    })
    panic_path = tmp_path / "panic.flag"
    monkeypatch.setattr(defense, "_panic_path", lambda: panic_path)
    if panic:
        panic_path.write_text("test panic", encoding="utf-8")
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_SECRET", "test-only-dsx-secret-material-32-bytes")
    monkeypatch.setenv("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")

    orchestrator = orchestrator_module.Orchestrator(fex_report_provider=provider)
    values = [100.0 + 0.1 * i for i in range(40)]
    state = orchestrator.ejecutar_ciclo(
        SensoryInput(
            precio_historico=values,
            precio_actual=values[-1],
            dynamic_constraints=dynamic_constraints or {},
        ),
        cycle_id="actual-orchestrator-synthetic-cycle",
    )
    return state, orchestrator.transductor.package


def test_acceptance_real_orchestrator_blocks_missing_fex_and_aex_handoff(monkeypatch, tmp_path):
    state, package = _run_real_orchestrator_cycle(monkeypatch, tmp_path, provider=None)
    policy = package["cognicion"]["operational_policy"]
    assert state.decision == "buy"
    assert policy["fex_report_status"] == "missing_fail_closed"
    assert policy["dsx_final_gate"]["blocked"] is True
    assert "sustainability_report_missing" in policy["dsx_final_gate"]["reasons"]
    assert policy["aex_review_intent"]["status"] == "BLOCKED_REVIEW_ONLY"
    assert policy["execution_handoff"]["trading_enabled"] is False
    assert policy["execution_handoff"]["orders_created"] is False
    assert policy["execution_handoff"]["orders_executed"] is False


def test_acceptance_real_orchestrator_passes_authenticated_fex_to_dsx_but_aex_stays_review_only(monkeypatch, tmp_path):
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad
    provider = lambda _financial, _cognitive, _price: evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    _state, package = _run_real_orchestrator_cycle(monkeypatch, tmp_path, provider=provider)
    policy = package["cognicion"]["operational_policy"]
    assert policy["fex_report_status"] == "provided"
    assert policy["dsx_final_gate"]["blocked"] is False
    assert policy["dsx_final_gate"]["dsx_signature"]
    assert policy["dsx_signature_valid"] is True
    assert policy["aex_review_intent"]["status"] == "BLOCKED_REVIEW_ONLY"
    assert "hold_signal" in policy["aex_review_intent"]["block_reasons"]
    assert "explicit_authorization_missing" in policy["aex_review_intent"]["block_reasons"]
    assert policy["aex_review_intent"]["trading_enabled"] is False
    assert policy["execution_handoff"]["orders_created"] is False
    assert policy["execution_handoff"]["orders_executed"] is False



def test_acceptance_dynamic_constraint_breach_forces_hold_and_is_reported(monkeypatch, tmp_path):
    constraints = {
        "reinvestment_surplus": 1.0,
        "entropy_rate": 2.0,
        "entropy_time_scale": 2.0,
        "loop_gain": 0.5,
        "signal_count": 2,
        "optimal_signal_count": 3,
        "exposure": 0.2,
        "max_exposure": 0.4,
        "resilience": 0.8,
        "minimum_resilience": 0.6,
    }
    state, package = _run_real_orchestrator_cycle(
        monkeypatch, tmp_path, dynamic_constraints=constraints
    )
    financial = package["percepcion_espacial"]["analisis_financiero"]
    report = package["contexto"]["dynamic_constraints"]
    assert state.decision == "hold"
    assert "dynamic_hard_constraint" in financial["risk_flags"]
    assert report["growth_allowed"] is False
    assert "MANTENIMIENTO_ENTROPICO" in report["issues"]
    assert package["contexto"]["trading_enabled"] is False
    assert package["contexto"]["orders_created"] is False


def test_acceptance_unknown_dynamic_constraint_key_fails_closed(monkeypatch, tmp_path):
    state, package = _run_real_orchestrator_cycle(
        monkeypatch, tmp_path, dynamic_constraints={"unrecognized_metric": 1.0}
    )
    report = package["contexto"]["dynamic_constraints"]
    assert state.decision == "hold"
    assert report["growth_allowed"] is False
    assert report["issues"] == ["CLAVES_DE_RESTRICCION_DESCONOCIDAS"]
    assert "dynamic_hard_constraint" in package["percepcion_espacial"]["analisis_financiero"]["risk_flags"]

def test_acceptance_real_orchestrator_rejects_tampered_fex_report(monkeypatch, tmp_path):
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad
    def forged_provider(_financial, _cognitive, _price):
        report = evaluar_restricciones_sostenibilidad(
            B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
            exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
        )
        report["metricas"]["loop_gain"] = 0.2
        return report
    _state, package = _run_real_orchestrator_cycle(monkeypatch, tmp_path, provider=forged_provider)
    policy = package["cognicion"]["operational_policy"]
    assert policy["dsx_final_gate"]["blocked"] is True
    assert "sustainability_evidence_integrity_failed" in policy["dsx_final_gate"]["reasons"]
    assert policy["aex_review_intent"]["status"] == "BLOCKED_REVIEW_ONLY"


def test_acceptance_real_orchestrator_rejects_expired_or_invalid_dsx_authorization(monkeypatch, tmp_path):
    import REASON.orchestrator as orchestrator_module
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad
    provider = lambda _financial, _cognitive, _price: evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    monkeypatch.setattr(orchestrator_module, "verificar_autorizacion_ejecucion", lambda *_args: False)
    _state, package = _run_real_orchestrator_cycle(monkeypatch, tmp_path, provider=provider)
    policy = package["cognicion"]["operational_policy"]
    assert policy["dsx_final_gate"]["blocked"] is False
    assert policy["dsx_signature_valid"] is False
    assert policy["execution_handoff"]["status"] == "BLOCKED"
    assert policy["aex_review_intent"]["status"] == "BLOCKED_REVIEW_ONLY"


def test_acceptance_real_orchestrator_emergency_panic_blocks_final_handoff(monkeypatch, tmp_path):
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad
    provider = lambda _financial, _cognitive, _price: evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    _state, package = _run_real_orchestrator_cycle(monkeypatch, tmp_path, provider=provider, panic=True)
    policy = package["cognicion"]["operational_policy"]
    assert policy["dsx_final_gate"]["blocked"] is True
    assert "panic_active" in policy["dsx_final_gate"]["reasons"]
    assert policy["aex_review_intent"]["status"] == "BLOCKED_REVIEW_ONLY"


def test_acceptance_fex_authentication_rejects_short_secret(monkeypatch):
    from DSX.DEFENSE.guards import sustainability_execution_guard
    from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad

    monkeypatch.setenv("CATEDRALX_FEX_EVIDENCE_SECRET", "too-short")
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    assert report["evidence_signature"] is None
    assert sustainability_execution_guard(report)["blocked"] is True
