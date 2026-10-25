"""DecisionResult builder for CatedralX (Fase 0)."""
import uuid
from datetime import datetime, timezone
from typing import Any

def build_decision_result(state: Any, cognitive: dict[str, Any], cycle_id: str | None = None) -> dict[str, Any]:
    trace_id = cycle_id or state.percepcion_espacial.get("cycle_id") or str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Determine status based on thresholds
    disonancia = cognitive.get("coherencia", {}).get("disonancia", 0.0) or 0.0
    contraevidencia = cognitive.get("contraevidencia", {}).get("fuerza_contra", 0.0) or 0.0
    
    status = "ACCEPTED"
    if disonancia > 0.8 or contraevidencia > 0.7:
        status = "REJECTED"
    elif disonancia > 0.4 or contraevidencia > 0.35:
        status = "UNCERTAIN"
        
    prov_records = cognitive.get("provenance", [])
    if isinstance(prov_records, dict) and "records" in prov_records:
        prov_records = prov_records["records"]
        
    evidence = []
    prov_ids = []
    for p in prov_records:
        if not isinstance(p, dict):
            continue
        prov_ids.append(p.get("id", ""))
        evidence.append({
            "evidence_id": p.get("id", str(uuid.uuid4())),
            "kind": "calculation",
            "source": p.get("module", "unknown"),
            "observed_at": now_iso,
            "digest": p.get("hash"),
            "notes": p.get("status", "")
        })
        
    risks = state.percepcion_espacial.get("analisis_financiero", {}).get("risk_flags", [])
    
    return {
        "result_id": str(uuid.uuid4()),
        "status": status,
        "engine": "CatedralX",
        "decision": state.decision,
        "evidence": evidence,
        "assumptions": [],
        "risks": risks,
        "tests": [],
        "provenance": prov_ids,
        "trace_id": trace_id,
        "analysis_only": True,
        "orders_created": False,
        "orders_executed": False,
        "next_action": "None" if status == "ACCEPTED" else "Manual review required"
    }
