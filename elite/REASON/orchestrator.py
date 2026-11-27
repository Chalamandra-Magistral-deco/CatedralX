#!/usr/bin/env python3
"""Main reasoning loop: reads PERCEIVE and writes the shared Cathedral state."""

import json
import math
import time
import uuid
from typing import Any

import numpy as np
from ENERGY.resource_governor import consume_cycle_budget
from AEX.ejecutor import preparar_intencion
from DSX.DEFENSE import defense
from DSX.DEFENSE.guards import (
    cognitive_execution_guard,
    final_execution_guard,
    verificar_autorizacion_ejecucion,
)
from FEX.FEEDBACK.feedback_loop import resumir_memoria_decisiones
from PERCEIVE.api_pulse import validate_snapshot_payload
from PERCEIVE.data_feeder import snapshot_path as rsx_snapshot_path

from . import anharmonic, cerebellum, free_energy, geometry, gyroscope, hurst_analyzer, mental_power
from .dynamic_constraints import DynamicConstraintInputs, evaluate_dynamic_constraints
from .financial_engine import analyze_financial_market
from .hamiltonian import HamiltonianEngine
from .procesador import TransductorEndocrino
from .report_composition import build_cognitive_report
from .schemas import CathedralState, SensoryInput
from .state_paths import canonical_state_path

SNAPSHOT_PATH = rsx_snapshot_path()  # CANONICO RSX desde data_feeder - consolidado Paso2
HAMILTONIAN_PROTECTION_LIMIT = 45.0


def construir_neurovector(
    gyro: dict[str, Any],
    geo: dict[str, Any],
    hurst: float,
    energia_libre: float,
) -> list[float]:
    """Build a compact state vector from the repository's dict-based outputs."""
    señal = geo.get("señal_combinada", "lateral")
    señal_valor = {"compra": 1.0, "venta": -1.0}.get(señal, 0.0)
    return [
        float(gyro.get("omega", 0.0)),
        float(gyro.get("precesion", 0.0)),
        float(gyro.get("estabilidad", 0.5)),
        señal_valor,
        float(hurst),
        float(energia_libre),
    ]


class Orchestrator:
    def __init__(self, fex_report_provider: Any = None) -> None:
        # FEX evidence must come from an explicit provider; never fabricate governance metrics.
        self.fex_report_provider = fex_report_provider
        state_path = canonical_state_path()
        self.transductor = TransductorEndocrino(output_path=state_path)
        self.ultimo_fe = 0.0
        self._gyro_filter_state = None
        # Bounded process-local context. No persistent learning or parameter updates.
        self._regime_history: list[str] = []
        self._decision_history: list[str] = []
        self.hamiltonian_engine = HamiltonianEngine()

    def _leer_snapshot_percibido(self) -> dict[str, Any]:
        try:
            return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _construir_sensory_input(self, datos_percibidos: dict[str, Any]) -> SensoryInput:
        perceive = datos_percibidos.get("PERCEIVE", {})
        if not isinstance(perceive, dict):
            raise ValueError("PERCEIVE debe ser un objeto con precios observados.")
        raw_prices = perceive.get("historial_precios", [])
        if not isinstance(raw_prices, list) or not raw_prices:
            raise ValueError("No hay historial de precios observado; se cancela el ciclo sin datos sintéticos.")
        precios: list[float] = []
        for index, value in enumerate(raw_prices):
            if isinstance(value, bool):
                raise ValueError(f"historial_precios[{index}] debe ser positivo y finito.")
            price = float(value)
            if not math.isfinite(price) or price <= 0:
                raise ValueError(f"historial_precios[{index}] debe ser positivo y finito.")
            precios.append(price)
        precio_actual = float(perceive.get("precio", precios[-1]))
        if not math.isfinite(precio_actual) or precio_actual <= 0:
            raise ValueError("PERCEIVE.precio debe ser positivo y finito.")
        if not precios or precios[-1] != precio_actual:
            precios.append(precio_actual)
        if len(precios) < 30:
            raise ValueError(f"Historial insuficiente: se requieren al menos 30 precios; hay {len(precios)}.")
        gap = float(perceive.get("gap", 0.0))
        inercia = float(perceive.get("inercia", 0.0))
        if not math.isfinite(gap) or not math.isfinite(inercia):
            raise ValueError("gap e inercia deben ser valores finitos.")
        from PERCEIVE.percepcion import validar_campos_gobernanza
        dynamic_constraints, central_dimensions_bp = validar_campos_gobernanza(datos_percibidos)
        return SensoryInput(
            precio_historico=precios,
            precio_actual=precio_actual,
            gap=gap,
            inercia=inercia,
            free_energy_prev=self.ultimo_fe,
            dynamic_constraints=dynamic_constraints,
            central_dimensions_bp=central_dimensions_bp,
        )

    def ejecutar_ciclo(
        self, entrada: SensoryInput, cycle_id: str | None = None
    ) -> CathedralState:
        """Run one financial-analysis cycle and persist only its canonical state."""
        cycle_id = cycle_id or str(uuid.uuid4())
        raw_prices = list(entrada.precio_historico)
        current = float(entrada.precio_actual)
        if not math.isfinite(current) or current <= 0:
            raise ValueError("precio_actual debe ser positivo y finito.")
        if raw_prices and raw_prices[-1] != current:
            raw_prices.append(current)

        # Financial validation happens before any cognitive state is advanced or saved.
        financial = analyze_financial_market(raw_prices)
        allowed_constraint_keys = set(DynamicConstraintInputs.__dataclass_fields__)
        supplied_constraints = entrada.dynamic_constraints
        if not isinstance(supplied_constraints, dict):
            supplied_constraints = {}
        unknown_constraint_keys = sorted(set(supplied_constraints) - allowed_constraint_keys)
        constraints_report: dict[str, Any]
        if unknown_constraint_keys:
            constraints_report = {
                "state": "RESTRICCIONES_NO_VERIFICADAS",
                "growth_allowed": False,
                "entropy_constraint_ok": False,
                "feedback_constraint_ok": False,
                "scale_constraint_ok": False,
                "issues": ["CLAVES_DE_RESTRICCION_DESCONOCIDAS"],
                "missing_metrics": [],
                "invalid_metrics": unknown_constraint_keys,
                "automatic_recalibration": False,
                "automatic_modularization": False,
            }
        else:
            constraints_report = evaluate_dynamic_constraints(
                DynamicConstraintInputs(**supplied_constraints)
            )
        measured_breach = any(issue in constraints_report["issues"] for issue in (
            "MANTENIMIENTO_ENTROPICO", "FRENO_DINAMICO",
            "MODULARIZAR_O_REDUCIR_EXPOSICION", "DATOS_INVALIDOS",
            "CLAVES_DE_RESTRICCION_DESCONOCIDAS",
        ))
        if measured_breach:
            financial["risk_flags"] = list(financial.get("risk_flags", []))
            if "dynamic_hard_constraint" not in financial["risk_flags"]:
                financial["risk_flags"].append("dynamic_hard_constraint")
            financial["signal"] = "hold"
            financial["combined_signal"] = "lateral"
            financial["signal_strength"] = 0.0
            financial["regime"] = "DYNAMIC_CONSTRAINT_HOLD"
            financial["decision_reason"] = (
                "Restricción dinámica dura activada; crecimiento bloqueado y requiere revisión."
            )
        prices = [float(value) for value in raw_prices]
        gap = float(entrada.gap)
        inertia = float(entrada.inercia)
        if not math.isfinite(gap) or not math.isfinite(inertia):
            raise ValueError("gap e inercia deben ser valores finitos.")

        h_val = hurst_analyzer.hurst_exponent(prices)
        cr_val, score_anarmonico = anharmonic.analyze(prices)
        giro = gyroscope.gyro_state(prices, self._gyro_filter_state)
        self._gyro_filter_state = giro.pop("_estado_filtro", None)

        volatility = float(np.std(np.diff(np.log(np.maximum(prices[-20:], 1e-12)))) if len(prices) > 20 else 0.01)
        retorno = float(np.log(max(prices[-1], 1e-12) / max(prices[-2], 1e-12))) if len(prices) > 1 else 0.0
        fe = free_energy.free_energy(
            prediccion_tendencia=0.5 + (h_val - 0.5),
            realidad_gap=abs(gap),
            inercia_observada=inertia,
            retorno_actual=retorno,
            coherencia_previa=free_energy.coherencia_desde_energia_previa(self.ultimo_fe),
        )
        self.ultimo_fe = fe

        direction = 1.0 if prices[-1] > prices[0] else -1.0 if prices[-1] < prices[0] else 0.0
        # The legacy qubit uses random sampling. Keep its diagnostic role but
        # use deterministic argmax in the canonical cycle so repeated analyses
        # of identical data do not persist different legacy labels.
        legacy_decision = cerebellum.colapsar_qubit_determinista(
            fuerza_tendencia=abs(h_val - 0.5) * 2.0,
            fuerza_rango=score_anarmonico,
            direccion=direction,
            cortisol=0.3,
        )
        legacy_confidence = round(max(abs(h_val - 0.5) * 2.0, score_anarmonico), 4)
        cognitive_load = mental_power.evaluate_stress(0.3, fe)
        hamiltonian = self.hamiltonian_engine.compute(
            {
                "volatilidad_local": volatility,
                "gap": gap,
                "sentimiento_riesgo": cognitive_load,
            }
        )

        # Hamiltonian protection is a review/hold gate, not an order to flatten:
        # position and portfolio context are not available to this analysis-only motor.
        if abs(hamiltonian) > HAMILTONIAN_PROTECTION_LIMIT:
            financial["risk_flags"] = list(financial["risk_flags"])
            if "hamiltonian_protection_triggered" not in financial["risk_flags"]:
                financial["risk_flags"].append("hamiltonian_protection_triggered")
            financial["signal"] = "hold"
            financial["combined_signal"] = "lateral"
            financial["regime"] = "RISK_PROTECTION_HOLD"
            financial["signal_strength"] = 0.0
            financial["decision_reason"] = (
                "Se bloqueó la etiqueta direccional por el umbral de protección "
                "hamiltoniana; se requiere revisión manual."
            )

        decision = str(financial["signal"])
        signal_strength = float(financial["signal_strength"])

        # SCX cognitive diagnostics use only explicit direction/confidence fields.
        # signal_strength is a heuristic, not a calibrated probability.
        gyro_direction = giro.get("orientacion")
        signals = [{
            "name": "financial_engine",
            "direction": decision,
            "confidence": signal_strength,
            "confidence_kind": "heuristic_signal_strength",
        }]
        if gyro_direction in {"ALCISTA", "BAJISTA", "NEUTRO"} and isinstance(giro.get("confianza"), (int, float)):
            signals.append({
                "name": "gyroscope",
                "direction": gyro_direction,
                "confidence": float(giro["confianza"]),
                "confidence_kind": "module_heuristic_confidence",
            })
        cognitive = build_cognitive_report(
            decision=decision,
            signals=signals,
            regime_history=[*self._regime_history, str(financial["regime"])][-100:],
            decision_history=[*self._decision_history, decision][-50:],
            input_evidence={
                "cycle_id": cycle_id,
                "price_count": len(prices),
                "latest_price": current,
                "financial_signal": decision,
                "signal_strength_is_probability": False,
                "gyroscope_orientation": gyro_direction,
                "gyroscope_confidence": giro.get("confianza"),
            },
        )
        # DSX owns enforcement; SCX only reports coherence and counterevidence.
        dsx_gate = cognitive_execution_guard(
            cognitive["coherencia"], cognitive["contraevidencia"],
            dissonance_threshold=0.40, counterevidence_threshold=0.35,
            panic=defense._panic_path().exists(),
        )
        cognitive["operational_policy"]["dsx_guard"] = dsx_gate
        cognitive["operational_policy"]["hard_block"] = dsx_gate["blocked"]
        # A measured contradiction is a hold/review gate, never an order.
        if dsx_gate["blocked"]:
            decision = "hold"
            financial["signal"] = "hold"
            financial["combined_signal"] = "lateral"
            financial["risk_flags"] = list(financial.get("risk_flags", []))
            if "cognitive_contradiction_review" not in financial["risk_flags"]:
                financial["risk_flags"].append("cognitive_contradiction_review")
            financial["decision_reason"] = (
                "La capa cognitiva detectó disonancia/contraevidencia sobre el umbral; "
                "el ciclo queda en HOLD para revisión."
            )
            cognitive["decision"] = decision
            cognitive["operational_policy"]["hard_block"] = True
            cognitive["operational_policy"]["status"] = "hold_for_review"

        # Actual cycle integration: SCX report + explicit FEX evidence -> final DSX gate -> AEX review-only stub.
        # Missing provider/report is deliberately fail-closed; no governance metrics are fabricated here.
        panic_active = defense._panic_path().exists()
        try:
            fex_report = self.fex_report_provider(financial, cognitive, current) if self.fex_report_provider else None
        except Exception as error:
            fex_report = None
            cognitive["operational_policy"]["fex_provider_error"] = type(error).__name__
        intent_context = {
            "accion": str(decision),
            "tamano": 0.0,
            "confianza": float(signal_strength),
            "razon": str(financial.get("decision_reason", "")),
        }
        dsx_final = final_execution_guard(
            cognitive["coherencia"], cognitive["contraevidencia"], fex_report,
            panic=panic_active, decision_context=intent_context, reference_price=current,
        )
        dsx_signature_valid = verificar_autorizacion_ejecucion(
            dsx_final, intent_context, current,
        )
        aex_risk_flags = list(financial.get("risk_flags", []))
        if dsx_final["blocked"]:
            aex_risk_flags.append("dsx_final_gate_blocked")
        if not dsx_signature_valid:
            aex_risk_flags.append("dsx_authorization_invalid_or_expired")
        # Review-only handoff is always HOLD with zero size; preserve the analytical
        # signal separately so it cannot be mistaken for an actionable order.
        aex_intent = preparar_intencion(
            "hold", size=0.0, panic=panic_active, risk_flags=aex_risk_flags,
        )
        aex_intent["requested_signal"] = decision
        # AEX only receives a review intent. This path never calls generar_orden/execute_order.
        cognitive["operational_policy"]["fex_report_status"] = (
            "provided" if isinstance(fex_report, dict) else "missing_fail_closed"
        )
        cognitive["operational_policy"]["dsx_final_gate"] = dsx_final
        cognitive["operational_policy"]["dsx_signature_valid"] = dsx_signature_valid
        cognitive["operational_policy"]["aex_review_intent"] = aex_intent
        cognitive["operational_policy"]["execution_handoff"] = {
            "cycle_id": cycle_id,
            "status": "BLOCKED" if dsx_final["blocked"] or not dsx_signature_valid else "REVIEW_REQUIRED",
            "trading_enabled": False,
            "orders_created": False,
            "orders_executed": False,
        }

        # Record the final observed cycle decision in bounded, process-local memory.
        self._regime_history.append(str(financial["regime"]))
        self._decision_history.append(decision)
        self._regime_history = self._regime_history[-100:]
        self._decision_history = self._decision_history[-50:]
        cognitive["memoria"] = resumir_memoria_decisiones(self._decision_history)
        cognitive["contexto"] = {
            **cognitive["contexto"],
            "historial_fases": list(self._regime_history),
            "memoria_status": "process_local_not_persistent",
        }

        decisions: list[dict[str, Any]] = []
        if decision == "buy" and not financial["risk_flags"]:
            decisions = [{
                "accion": "COMPRAR",
                "confianza": signal_strength,
                "modo": "ANALISIS_FINANCIERO",
            }]
        elif decision == "sell" and not financial["risk_flags"]:
            decisions = [{
                "accion": "VENDER",
                "confianza": signal_strength,
                "modo": "ANALISIS_FINANCIERO",
            }]

        package: dict[str, Any] = {
            "cycle_id": cycle_id,
            "timestamp": int(time.time()),
            "economic_feedback": {
                "status": "not_evaluated",
                "reason": "verified_business_ledger_not_provided",
                "money_moved": False,
                "payments_executed": False,
            },
            "contexto": {
                "cycle_id": cycle_id,
                "market_phase": financial["regime"],
                "geometry_regime": "ELIPTICO" if score_anarmonico > 0.6 else "HIPERBOLICO",
                "señal_combinada": financial["combined_signal"],
                "last_decision": decision,
                "decision_financiera": decision,
                "decision_subsistema_original": legacy_decision,
                "confianza_subsistema_original": legacy_confidence,
                "decision_subsistema_original_rol": "diagnostico_no_autoritativo",
                "decision_subsistema_original_es_estocastico": False,
                "signal_strength": signal_strength,
                "signal_strength_is_probability": False,
                "financial_risk_flags": financial["risk_flags"],
                "carga_mental": cognitive_load,
                "hamiltoniano": hamiltonian,
                "modo": "PROTECCION" if financial["risk_flags"] else "ANALISIS_FINANCIERO",
                "trading_enabled": False,
                "orders_created": False,
                "orders_executed": False,
                "dynamic_constraints": constraints_report,
                "growth_allowed": constraints_report["growth_allowed"],
            },
            "percepcion_espacial": {
                "hurst": round(h_val, 4),
                "gap_detectado": round(gap, 6),
                "inercia": round(inertia, 6),
                "free_energy": round(fe, 4),
                "analisis_financiero": financial,
                "dynamic_constraints": constraints_report,
                "growth_allowed": constraints_report["growth_allowed"],
                "decision_subsistema_original": legacy_decision,
                "decision_subsistema_original_rol": "diagnostico_no_autoritativo",
                "decision_subsistema_original_es_estocastico": False,
            },
            "giroscopio": giro,
            "razon_anarmonica": {
                "cross_ratio": round(cr_val, 6),
                "score": round(score_anarmonico, 4),
                "senal": legacy_decision,
                "zona": "estable" if score_anarmonico > 0.7 else "indefinido",
            },
            "cognicion": cognitive,
        }
        self.transductor.volcar_estado_quimico(package)
        state = CathedralState(
            int(time.time()),
            decision,
            signal_strength,
            round(fe, 4),
            self.transductor.leer_estado_actual().get("concentracion_actual", {}),
            giro,
            package["razon_anarmonica"],
            package["percepcion_espacial"],
            hamiltonian,
            cognitive_load,
        )
        state.decisiones = decisions
        state.cognicion = cognitive
        state.regimen = str(financial["regime"])
        state.señal_combinada = str(financial["combined_signal"])
        state.percepcion_espacial["cycle_id"] = cycle_id
        return state

    def bucle_infinito(self) -> None:
        """Continuously analyze validated input without modifying its snapshot."""
        print("CatedralX Motor Financiero v1 - análisis sin ejecución de órdenes")
        while True:
            try:
                datos = self._leer_snapshot_percibido()
                if not datos:
                    time.sleep(2)
                    continue

                freshness = validate_snapshot_payload(datos)
                if not freshness["healthy"]:
                    print(
                        "Ciclo omitido: snapshot rechazado "
                        f"({freshness['reason']})"
                    )
                    time.sleep(2)
                    continue

                entrada = self._construir_sensory_input(datos)
                estado = execute_cycle(entrada)
                hurst = estado.percepcion_espacial.get("hurst", 0.5)
                print(
                    f"Ciclo completado | Decision: {estado.decision} "
                    f"| Hurst: {hurst:.4f}"
                )
                time.sleep(3)
            except Exception as error:
                print(f"Error en ciclo: {error}")
                time.sleep(2)


def execute_cycle(
    sensory_data: SensoryInput,
    cycle_id: str | None = None,
    *,
    trace_id: str | None = None,
) -> CathedralState:
    """Run one analysis with shared cycle and W3C trace identifiers."""
    identifier = cycle_id or str(uuid.uuid4())
    trace_identifier = uuid.uuid4().hex if trace_id is None else trace_id
    if (
        not isinstance(trace_identifier, str)
        or len(trace_identifier) != 32
        or any(char not in "0123456789abcdef" for char in trace_identifier)
        or trace_identifier == "0" * 32
    ):
        raise ValueError("trace_id debe ser un W3C trace ID hexadecimal de 32 caracteres")
    # DSX resource gate: a cycle cannot start without operational budget.
    # Credits are virtual compute quotas, not physical/electrical energy.
    energy_receipt, energy_snapshot, energy_ledger_record = consume_cycle_budget(identifier)
    state = think(
        sensory_data, sensory_data.precio_historico, identifier,
        trace_id=trace_identifier,
    )
    state.percepcion_espacial["trace_id"] = trace_identifier

    # MSX cycle evidence: persistable provenance records are attached to the
    # same DecisionResult consumed by the append-only result store.
    from MSX.provenance import aggregate_cycle, build_provenance

    energy_record = build_provenance(
        "resource_budget_authorization",
        "DSX",
        "1",
        {
            "cycle_id": identifier,
            "trace_id": trace_identifier,
            "transaction_id": energy_receipt.transaction_id,
            "reservoir": energy_receipt.reservoir,
            "credits_spent": energy_receipt.amount,
            "ledger_sequence": energy_ledger_record["sequence"],
            "ledger_record_hash": energy_ledger_record["record_hash"],
        },
        output={
            "authorized": True,
            "operational_balance": energy_receipt.balance,
            "state_of_charge": energy_snapshot["state_of_charge"],
            "adaptive_balance": energy_snapshot["adaptive"].charge,
        },
        vector="DSX",
        status="authorized",
    )
    sensory_record = build_provenance(
        "sensory_observation",
        "PERCEIVE",
        "1",
        {
            "cycle_id": identifier,
            "trace_id": trace_identifier,
            "price_count": len(sensory_data.precio_historico),
            "current_price": float(sensory_data.precio_actual),
            "gap": float(sensory_data.gap),
            "inertia": float(sensory_data.inercia),
        },
        output={"accepted_for_reasoning": True},
        vector="RSX",
        status="observed",
    )
    reasoning_record = build_provenance(
        "reasoning_result",
        "REASON",
        "1",
        {
            "cycle_id": identifier,
            "trace_id": trace_identifier,
            "sensory_record_id": sensory_record["id"],
        },
        output={
            "decision": state.decision,
            "free_energy": float(state.free_energy),
            "hamiltonian": float(state.hamiltoniano),
            "signal_strength": float(state.confianza),
            "regime": str(state.regimen),
        },
        vector="SCX",
        parent=sensory_record["id"],
        status="computed",
    )
    cognitive = state.cognicion if isinstance(state.cognicion, dict) else {}
    policy = cognitive.get("operational_policy", {})
    if not isinstance(policy, dict):
        policy = {}
    dsx_record = build_provenance(
        "safety_regulation",
        "DSX",
        "1",
        {
            "cycle_id": identifier,
            "trace_id": trace_identifier,
            "reasoning_record_id": reasoning_record["id"],
        },
        output={
            "hard_block": bool(policy.get("hard_block", True)),
            "execution_handoff": policy.get("execution_handoff", {
                "status": "UNVERIFIED",
                "trading_enabled": False,
                "orders_created": False,
                "orders_executed": False,
            }),
        },
        vector="DSX",
        parent=reasoning_record["id"],
        status="regulated",
    )
    records = [energy_record, sensory_record, reasoning_record, dsx_record]
    cognitive["resource_budget"] = {
        "status": "authorized",
        "transaction_id": energy_receipt.transaction_id,
        "credits_spent": energy_receipt.amount,
        "operational_balance": energy_receipt.balance,
        "adaptive_balance": energy_snapshot["adaptive"].charge,
        "state_of_charge": energy_snapshot["state_of_charge"],
        "unit": "virtual_compute_credit",
        "durability": "msx_hash_chained_jsonl",
        "ledger_sequence": energy_ledger_record["sequence"],
        "ledger_record_hash": energy_ledger_record["record_hash"],
    }
    cognitive["provenance"] = records
    cognitive["cycle_trace"] = aggregate_cycle(identifier, records)
    state.cognicion = cognitive
    return state

class _LazyOrchestrator:
    """Defer shared state loading until a caller actually runs an orchestration cycle."""

    def __init__(self) -> None:
        object.__setattr__(self, "_instance", None)

    def _get_instance(self) -> Orchestrator:
        instance = object.__getattribute__(self, "_instance")
        if instance is None:
            instance = Orchestrator()
            object.__setattr__(self, "_instance", instance)
        return instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_instance":
            object.__setattr__(self, name, value)
        else:
            setattr(self._get_instance(), name, value)


_think_orchestrator = _LazyOrchestrator()


def think(
    sensory_input: SensoryInput,
    historial_precios: list[float],
    ciclo_id: str,
    *,
    trace_id: str | None = None,
) -> CathedralState:
    """Run deterministic financial analysis plus optional geometry diagnostics."""
    raw_prices = list(historial_precios)
    current = float(sensory_input.precio_actual)
    if not math.isfinite(current) or current <= 0:
        raise ValueError("precio_actual debe ser positivo y finito.")
    if raw_prices and raw_prices[-1] != current:
        raw_prices.append(current)
    gap_value = float(sensory_input.gap)
    inertia_value = float(sensory_input.inercia)
    if not math.isfinite(gap_value) or not math.isfinite(inertia_value):
        raise ValueError("gap e inercia deben ser valores finitos.")

    entrada = SensoryInput(
        precio_historico=raw_prices,
        precio_actual=current,
        gap=gap_value,
        inercia=inertia_value,
        free_energy_prev=sensory_input.free_energy_prev,
        dynamic_constraints=dict(sensory_input.dynamic_constraints),
        central_dimensions_bp=dict(sensory_input.central_dimensions_bp),
    )
    # ejecutar_ciclo validates financial inputs before touching persistent state.
    state = _think_orchestrator.ejecutar_ciclo(entrada, cycle_id=ciclo_id)
    # Financial validation has passed in ejecutar_ciclo; normalize only for diagnostics.
    prices = [float(value) for value in raw_prices]
    try:
        geo_state = geometry.analyze_geometry(prices)
    except Exception as exc:
        # The financial output remains usable if this exploratory diagnostic fails.
        geo_state = {
            "regimen": "INDEFINIDO",
            "señal_combinada": "lateral",
            "diagnostic_error": type(exc).__name__,
        }
    neurovector = construir_neurovector(
        state.giroscopio,
        geo_state,
        state.percepcion_espacial.get("hurst", 0.5),
        state.free_energy,
    )
    state.neurovector = neurovector
    state.percepcion_espacial["diagnostico_geometrico"] = {
        key: value for key, value in geo_state.items() if key != "diagnostic_error"
    }
    if "diagnostic_error" in geo_state:
        state.percepcion_espacial["diagnostico_geometrico_error"] = geo_state["diagnostic_error"]
    state.percepcion_espacial["ciclo_id"] = ciclo_id
    state.percepcion_espacial["cycle_id"] = ciclo_id
    if trace_id is not None:
        state.percepcion_espacial["trace_id"] = trace_id
    state.percepcion_espacial["neurovector"] = neurovector
    # Preserve upstream governance inputs without deriving or recalibrating them.
    state.percepcion_espacial["central_dimensions_bp"] = dict(
        sensory_input.central_dimensions_bp
    )
    state.percepcion_espacial["dynamic_constraints_input"] = dict(
        sensory_input.dynamic_constraints
    )

    # --- REGLA CENTRAL (Catedral) ---
    try:
        from REASON.multicriteria import CathedralEvaluation

        # Every scored dimension must be supplied explicitly in integer basis points.
        # A market direction is not a measurement of economic viability.
        central_dimensions = state.percepcion_espacial.get("central_dimensions_bp", {})
        if not isinstance(central_dimensions, dict):
            central_dimensions = {}

        # Missing governance is a block, not permission. The central rule consumes
        # the dynamic-governance report; it does not infer calibration from defaults.
        constraints = state.percepcion_espacial.get("dynamic_constraints", {})
        dynamic_inputs = state.percepcion_espacial.get("dynamic_constraints_input", {})
        if not isinstance(dynamic_inputs, dict):
            dynamic_inputs = {}
        if not isinstance(constraints, dict) or constraints.get("growth_allowed") is not True:
            raw_reasons = constraints.get("issues", []) if isinstance(constraints, dict) else []
            blocking_reasons = [str(reason) for reason in raw_reasons if str(reason)]
            if not blocking_reasons:
                blocking_reasons = ["DYNAMIC_GOVERNANCE_NOT_VERIFIED"]
        else:
            blocking_reasons = []

        engine = CathedralEvaluation(
            viability=central_dimensions.get("viability_bp"),
            human_value=central_dimensions.get("human_value_bp"),
            distribution=central_dimensions.get("distribution_bp"),
            reinvestment=dynamic_inputs.get("reinvestment_surplus"),
            resilience=central_dimensions.get("resilience_bp"),
            evidence=central_dimensions.get("evidence_bp"),
        )
        verdict = engine.evaluate(blocking_reasons=blocking_reasons)
        state.cognicion["cathedral_verdict"] = verdict
    except Exception as e:
        # Fail-safe: evaluation errors are blocked and hashed, never accepted.
        try:
            from REASON.multicriteria import blocked_uncertainty

            state.cognicion["cathedral_verdict"] = blocked_uncertainty(
                reason="EVALUATION_ERROR",
                next_action="REVISAR_LOGS",
                blocking_reasons=[type(e).__name__],
            )
        except Exception:
            # If the central rule itself cannot be imported, preserve an explicit
            # blocked state. The result contract will reject it without a hash.
            state.cognicion["cathedral_verdict"] = {
                "status": "BLOCKED_UNCERTAINTY",
                "reason": "CENTRAL_RULE_UNAVAILABLE",
                "next_action": "REVISAR_LOGS",
            }

    return state

if __name__ == "__main__":
    _think_orchestrator.bucle_infinito()
