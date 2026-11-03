"""DSX enforcement gates. Consume SCX diagnostics; do not recalculate them."""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import time
from typing import Any

from FEX.GOVERNANCE.sustainability import verificar_integridad_evidencia

DSX_AUTH_TTL_SECONDS = 30
DSX_AUTH_KEYRING_ENV = "CATEDRALX_DSX_AUTH_KEYRING"
DSX_AUTH_ACTIVE_KEY_ID_ENV = "CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID"


def _dsx_auth_keyring() -> tuple[str, dict[str, bytes]]:
    """Load a versioned keyring; the active key signs, all configured keys verify during rotation."""
    raw_ring = os.environ.get(DSX_AUTH_KEYRING_ENV, "")
    active_id = os.environ.get(DSX_AUTH_ACTIVE_KEY_ID_ENV, "")
    if raw_ring:
        try:
            parsed = json.loads(raw_ring)
        except (TypeError, ValueError) as exc:
            raise PermissionError("Keyring DSX inválido; autorización bloqueada") from exc
        if not isinstance(parsed, dict) or not active_id or active_id not in parsed:
            raise PermissionError("Keyring DSX sin clave activa válida; autorización bloqueada")
        keys = {}
        for key_id, secret in parsed.items():
            if not isinstance(key_id, str) or not key_id or not isinstance(secret, str) or len(secret.encode("utf-8")) < 32:
                raise PermissionError("Keyring DSX contiene clave inválida; autorización bloqueada")
            keys[key_id] = secret.encode("utf-8")
        return active_id, keys
    # Compatibility mode for existing deployments/tests; migration to keyring is required.
    legacy = os.environ.get("CATEDRALX_DSX_AUTH_SECRET", "").encode("utf-8")
    if len(legacy) < 32:
        raise PermissionError("Autorización DSX bloqueada: configure keyring versionado o CATEDRALX_DSX_AUTH_SECRET con al menos 32 bytes")
    return "legacy", {"legacy": legacy}


def _dsx_auth_key(key_id: str | None = None) -> bytes:
    active_id, keys = _dsx_auth_keyring()
    selected = active_id if key_id is None else key_id
    if selected not in keys:
        raise PermissionError("Clave DSX desconocida o retirada; autorización bloqueada")
    return keys[selected]


def _decision_context(decision: dict[str, Any], price: float) -> str:
    payload = {
        "accion": str(decision.get("accion", "")),
        "tamano": float(decision.get("tamano", 0.0)),
        "confianza": float(decision.get("confianza", 0.0)),
        "razon_hash": hashlib.sha256(str(decision.get("razon", "")).encode("utf-8")).hexdigest(),
        "precio_actual": float(price),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _authorization_signature(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    key_id = payload.get("key_id")
    return hmac.new(_dsx_auth_key(key_id if isinstance(key_id, str) else None), canonical, hashlib.sha256).hexdigest()


def verificar_autorizacion_ejecucion(authorization: Any, decision: dict[str, Any], price: float) -> bool:
    """Verify DSX provenance, TTL and binding to the exact pending-order intent."""
    if not isinstance(authorization, dict):
        return False
    payload = authorization.get("dsx_signed_payload")
    signature = authorization.get("dsx_signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        return False
    try:
        expected = _authorization_signature(payload)
        issued = payload.get("issued_at")
        return bool(
            hmac.compare_digest(signature, expected)
            and payload.get("context_hash") == _decision_context(decision, price)
            and isinstance(issued, int) and 0 <= int(time.time()) - issued <= DSX_AUTH_TTL_SECONDS
            and payload.get("allowed") is True and payload.get("blocked") is False
            and payload.get("enforcement_vector") == "DSX"
            and payload.get("governance_status") == "verified"
            and payload.get("governance_metrics_complete") is True
            and payload.get("financial_execution_authorized") is False
        )
    except (TypeError, ValueError, OverflowError, PermissionError):
        return False


MANDATORY_GOVERNANCE_METRICS = (
    "reinvestment_surplus", "entropy_rate", "entropy_time_scale", "loop_gain",
    "signal_count", "optimal_signal_count", "exposure", "max_exposure",
    "resilience", "minimum_resilience",
)
_COUNT_METRICS = {"signal_count", "optimal_signal_count"}


def cognitive_execution_guard(coherence: dict[str, Any],
                              counterevidence: dict[str, Any],
                              *, dissonance_threshold: float = 0.40,
                              counterevidence_threshold: float = 0.35,
                              panic: bool = False) -> dict[str, Any]:
    """Fail closed on explicit cognitive contradiction, panic, or missing evidence."""
    if not 0 <= dissonance_threshold <= 1 or not 0 <= counterevidence_threshold <= 1:
        raise ValueError("umbrales deben estar entre 0 y 1")
    dissonance = coherence.get("disonancia")
    force = counterevidence.get("fuerza_contra")
    reasons = []
    if panic:
        reasons.append("panic_active")
    if dissonance is not None:
        if (not isinstance(dissonance, (int, float)) or isinstance(dissonance, bool)
                or not math.isfinite(float(dissonance)) or not 0.0 <= float(dissonance) <= 1.0):
            reasons.append("invalid_dissonance_evidence")
        elif dissonance > dissonance_threshold:
            reasons.append("high_dissonance")
    # Insufficient pairwise evidence is not itself contradiction; keep the status
    # explicit and reserve this gate for measured dissonance or panic.
    if force is not None:
        if (not isinstance(force, (int, float)) or isinstance(force, bool)
                or not math.isfinite(float(force)) or not 0.0 <= float(force) <= 1.0):
            reasons.append("invalid_counterevidence")
        elif force > counterevidence_threshold:
            reasons.append("counterevidence_threshold_exceeded")
    elif counterevidence.get("evidence_status") not in {"computed", "no_opposing_signal_observed"}:
        reasons.append("counterevidence_unavailable")
    blocked = bool(reasons)
    return {"allowed": not blocked, "blocked": blocked, "reasons": reasons,
            "dissonance_threshold": dissonance_threshold,
            "counterevidence_threshold": counterevidence_threshold,
            "enforcement_vector": "DSX"}


def sustainability_execution_guard(report: dict[str, Any] | None, *, panic: bool = False) -> dict[str, Any]:
    """Enforce the FEX sustainability report without recalculating its constraints.

    Missing, malformed, or failed evidence blocks by default. A passing report
    permits consideration of an action but never authorizes financial execution.
    """
    reasons: list[str] = []
    if panic:
        reasons.append("panic_active")
    if not isinstance(report, dict):
        reasons.append("sustainability_report_missing")
        report = {}
    elif not verificar_integridad_evidencia(report):
        reasons.append("sustainability_evidence_integrity_failed")

    metrics = report.get("metricas")
    if not isinstance(metrics, dict):
        reasons.append("mandatory_metrics_missing")
        metrics = {}
    missing = [name for name in MANDATORY_GOVERNANCE_METRICS if name not in metrics]
    if missing:
        reasons.append("mandatory_metrics_missing")
    else:
        invalid = []
        for name in MANDATORY_GOVERNANCE_METRICS:
            value = metrics[name]
            if name in _COUNT_METRICS:
                valid = isinstance(value, int) and not isinstance(value, bool) and value >= 0
            else:
                valid = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and value >= 0
            if not valid:
                invalid.append(name)
        if invalid:
            reasons.append("mandatory_metrics_invalid")

    if report.get("estado") != "CONTINUAR" or report.get("crecimiento_permitido") is not True or report.get("fallos") != []:
        reasons.append("sustainability_constraints_failed")
    if report.get("ejecucion_financiera_autorizada") is not False:
        reasons.append("invalid_financial_authorization_state")

    blocked = bool(reasons)
    return {"allowed": not blocked, "blocked": blocked, "reasons": reasons,
            "governance_status": "verified" if not blocked else "blocked_or_unverified",
            "governance_metrics_complete": not any(reason in reasons for reason in
                ("mandatory_metrics_missing", "mandatory_metrics_invalid")),
            "financial_execution_authorized": False, "enforcement_vector": "DSX"}


def final_execution_guard(coherence: dict[str, Any], counterevidence: dict[str, Any],
                          sustainability_report: dict[str, Any] | None, *, panic: bool = False,
                          decision_context: dict[str, Any] | None = None,
                          reference_price: float | None = None) -> dict[str, Any]:
    """Combine cognitive and sustainability gates into one DSX authorization result."""
    cognitive = cognitive_execution_guard(coherence, counterevidence, panic=panic)
    sustainability = sustainability_execution_guard(sustainability_report, panic=panic)
    reasons = list(dict.fromkeys(cognitive["reasons"] + sustainability["reasons"]))
    blocked = cognitive["blocked"] or sustainability["blocked"]
    result = {"allowed": not blocked, "blocked": blocked, "reasons": reasons,
              "enforcement_vector": "DSX",
              "governance_status": sustainability["governance_status"],
              "governance_metrics_complete": sustainability["governance_metrics_complete"],
              "financial_execution_authorized": False,
              "cognitive_gate": cognitive, "sustainability_gate": sustainability}
    # Only issue an order-bound, short-lived signed artifact for an explicit
    # passing gate. An unsigned dictionary is diagnostic output, not authority.
    if not blocked and isinstance(decision_context, dict) and reference_price is not None:
        try:
            active_key_id, _ = _dsx_auth_keyring()
            payload = {
                "key_id": active_key_id,
                "allowed": True, "blocked": False, "enforcement_vector": "DSX",
                "governance_status": sustainability["governance_status"],
                "governance_metrics_complete": sustainability["governance_metrics_complete"],
                "financial_execution_authorized": False,
                "context_hash": _decision_context(decision_context, reference_price),
                "issued_at": int(time.time()),
            }
            result["dsx_signed_payload"] = payload
            result["dsx_signature"] = _authorization_signature(payload)
        except (TypeError, ValueError, OverflowError, PermissionError):
            result["allowed"] = False
            result["blocked"] = True
            result["reasons"] = list(dict.fromkeys(reasons + ["dsx_signing_unavailable"]))
    return result
