"""One-shot SCX entry point. Requires a real, validated RSX snapshot."""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

ELITE_DIR = Path(__file__).resolve().parents[1]
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))

from contracts.builder import build_decision_result
from contracts.result_store import append_result
from DSX.DEFENSE import defense
from FEX.FEEDBACK.feedback_loop import registrar_prediccion
from PERCEIVE.api_pulse import validate_snapshot_payload
from PERCEIVE.data_feeder import snapshot_path
from PERCEIVE.percepcion import from_snapshot

from REASON.orchestrator import execute_cycle


def _no_cycle(reason: str) -> int:
    print(json.dumps({
        "status": "NO_CYCLE",
        "reason": reason,
        "trading_enabled": False,
        "orders_created": False,
        "orders_executed": False,
    }, ensure_ascii=False, indent=2))
    return 2


def main() -> int:
    panic_path = Path(defense.PATH_PANIC).expanduser()
    if panic_path.exists():
        return _no_cycle(f"Bloqueo de emergencia activo: {panic_path}")

    path = snapshot_path()  # CANONICO RSX consolidado Paso2
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        freshness = validate_snapshot_payload(snapshot)
        if not freshness["healthy"]:
            raise ValueError("Snapshot rechazado: " + str(freshness["reason"]))
        sensory = from_snapshot(snapshot)
        trace_id = os.getenv("CATEDRALX_TRACE_ID") or uuid.uuid4().hex
        state = execute_cycle(sensory, trace_id=trace_id)
    except (OSError, ValueError, TypeError) as exc:
        return _no_cycle(str(exc))

    financial = state.percepcion_espacial.get("analisis_financiero", {})
    result = {
        "status": "ANALYSIS_COMPLETE",
        "cycle_id": state.percepcion_espacial.get("cycle_id"),
        "decision": state.decision,
        "signal_strength": state.confianza,
        "signal_strength_is_probability": False,
        "regime": state.regimen,
        "combined_signal": state.señal_combinada,
        "hurst": state.percepcion_espacial.get("hurst"),
        "free_energy": state.free_energy,
        "financial_analysis": financial,
        "reference_price": snapshot["PERCEIVE"].get("precio"),
        "observed_at": snapshot["PERCEIVE"].get("observed_at"),
        "market_source": snapshot["PERCEIVE"].get("source"),
        "legacy_diagnostic_signal": state.percepcion_espacial.get("decision_subsistema_original"),
        "legacy_diagnostic_role": "diagnostico_no_autoritativo",
        "legacy_diagnostic_is_stochastic": False,
        "trading_enabled": False,
        "orders_created": False,
        "orders_executed": False,
        "trace_id": trace_id,
    }
    # FASE 1a: Generar contrato DecisionResult y persistir antes de feedback.
    cognitive_data = state.cognicion if hasattr(state, "cognicion") else {}
    decision_contract = build_decision_result(
        state,
        cognitive_data,
        cycle_id=state.percepcion_espacial.get("cycle_id"),
        trace_id=trace_id,
    )
    append_result(decision_contract)
    result["decision_result"] = decision_contract
    # FEX is downstream of durable DecisionResult persistence: a feedback
    # failure can no longer leave an orphan prediction without its contract.
    try:
        result["prediction_id"] = registrar_prediccion(result)
        result["feedback_status"] = "RECORDED"
    except Exception as exc:
        result["feedback_status"] = "FAILED"
        result["feedback_error"] = type(exc).__name__
    result["evaluation_hash"] = decision_contract.get("evaluation_hash")
    result["evaluation_gate"] = decision_contract.get("evaluation_gate")
    result["trace_id"] = decision_contract.get("trace_id")

    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
