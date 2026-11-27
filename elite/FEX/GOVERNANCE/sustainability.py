"""Fail-closed sustainability constraint evaluator for CatedralX.

This module computes governance state only. It does not recalibrate models,
change exposure, create orders, or execute financial actions. Callers must treat
ValueError as a blocked cycle and must not proceed with growth on invalid input.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from typing import Any

CONTINUE = "CONTINUAR"
MAINTENANCE = "MANTENIMIENTO"
DYNAMIC_BRAKE = "FRENO_DINAMICO"
MODULARIZE = "MODULARIZAR"


_EVIDENCE_FIELDS = ("estado", "fallos", "crecimiento_permitido",
                    "ejecucion_financiera_autorizada", "metricas")


def hash_evidencia_sostenibilidad(report: dict[str, Any]) -> str:
    """Hash the canonical FEX result fields; DSX can verify integrity without recomputing constraints."""
    payload = {key: report.get(key) for key in _EVIDENCE_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


FEX_ACTIVE_KEY_ID_ENV = "CATEDRALX_FEX_ACTIVE_KEY_ID"
FEX_KEYRING_ENV = "CATEDRALX_FEX_KEYRING"


def _fex_evidence_keyring() -> tuple[str, dict[str, bytes]]:
    """Versioned FEX keyring: active key signs and configured overlap keys verify during rotation."""
    raw_ring = os.environ.get(FEX_KEYRING_ENV, "")
    active_id = os.environ.get(FEX_ACTIVE_KEY_ID_ENV, "")
    if raw_ring:
        try:
            parsed = json.loads(raw_ring)
        except (TypeError, ValueError) as exc:
            raise PermissionError("Keyring FEX inválido; evidencia bloqueada") from exc
        if not isinstance(parsed, dict) or not active_id or active_id not in parsed:
            raise PermissionError("Keyring FEX sin clave activa válida; evidencia bloqueada")
        keys = {}
        for key_id, secret in parsed.items():
            if not isinstance(key_id, str) or not key_id or not isinstance(secret, str) or len(secret.encode("utf-8")) < 32:
                raise PermissionError("Keyring FEX contiene clave inválida; evidencia bloqueada")
            keys[key_id] = secret.encode("utf-8")
        return active_id, keys
    legacy = os.environ.get("CATEDRALX_FEX_EVIDENCE_SECRET", "").encode("utf-8")
    if len(legacy) < 32:
        raise PermissionError("Evidencia FEX no autenticada: configure keyring versionado o CATEDRALX_FEX_EVIDENCE_SECRET con al menos 32 bytes")
    return "legacy", {"legacy": legacy}


def _fex_evidence_key(key_id: str | None = None) -> bytes:
    active_id, keys = _fex_evidence_keyring()
    selected = active_id if key_id is None else key_id
    if selected not in keys:
        raise PermissionError("Clave FEX desconocida o retirada; evidencia bloqueada")
    return keys[selected]


def _firma_evidencia(report: dict[str, Any]) -> str:
    key_id = report.get("evidence_key_id")
    payload = {"evidence_hash": hash_evidencia_sostenibilidad(report)}
    if isinstance(key_id, str):
        payload["key_id"] = key_id
        key = _fex_evidence_key(key_id)
    else:
        key = _fex_evidence_key()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


def verificar_integridad_evidencia(report: Any) -> bool:
    """Verify FEX content integrity AND producer authenticity; fail closed without a key."""
    if not isinstance(report, dict) or not isinstance(report.get("evidence_hash"), str):
        return False
    signature = report.get("evidence_signature")
    if not isinstance(signature, str):
        return False
    try:
        expected_hash = hash_evidencia_sostenibilidad(report)
        if not hmac.compare_digest(report["evidence_hash"], expected_hash):
            return False
        if isinstance(report.get("evidence_key_id"), str):
            expected_signature = _firma_evidencia(report)
            return hmac.compare_digest(signature, expected_signature)

        _, keys = _fex_evidence_keyring()
        canonical = json.dumps(
            {"evidence_hash": expected_hash},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        return any(
            hmac.compare_digest(
                signature, hmac.new(key, canonical, hashlib.sha256).hexdigest()
            )
            for key in keys.values()
        )
    except (TypeError, ValueError, PermissionError):
        return False


def _finite_nonnegative(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} debe ser un número finito no negativo.")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} debe ser un número finito no negativo.")
    return number


def _count(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} debe ser un entero no negativo.")
    return value


def evaluar_restricciones_sostenibilidad(
    *,
    B: float,
    T: float,
    dSdt: float,
    G: float,
    N: int,
    N_star: int,
    exposicion: float,
    E_max: float,
    resiliencia: float,
    R_min: float,
    varianza_creciente: bool = False,
    recuperacion_lenta: bool = False,
) -> dict[str, Any]:
    """Evaluate three hard constraints without performing any action.

    Priority for the primary state: maintenance, dynamic brake, modularization,
    then continue. All failing constraints are returned in ``fallos``. The two
    early-warning flags together also activate the dynamic brake.
    """
    b = _finite_nonnegative(B, "B")
    t = _finite_nonnegative(T, "T")
    entropy_rate = _finite_nonnegative(dSdt, "dSdt")
    gain = _finite_nonnegative(G, "G")
    modules = _count(N, "N")
    optimal_modules = _count(N_star, "N_star")
    exposure = _finite_nonnegative(exposicion, "exposicion")
    exposure_limit = _finite_nonnegative(E_max, "E_max")
    resilience_value = _finite_nonnegative(resiliencia, "resiliencia")
    resilience_min = _finite_nonnegative(R_min, "R_min")

    if not isinstance(varianza_creciente, bool):
        raise ValueError("varianza_creciente debe ser booleano.")
    if not isinstance(recuperacion_lenta, bool):
        raise ValueError("recuperacion_lenta debe ser booleano.")

    mantenimiento_requerido = t * entropy_rate
    if not math.isfinite(mantenimiento_requerido):
        raise ValueError("T * dSdt debe ser finito.")

    fallos: list[str] = []
    alertas: list[str] = []
    acciones: list[str] = []

    # 1. Entropy / maintenance: reinvestment must cover estimated wear.
    if b < mantenimiento_requerido:
        fallos.append(MAINTENANCE)
        acciones.append("Cubrir mantenimiento y revisar desajuste de parámetros.")

    # 2. Feedback stability and early-warning indicators.
    early_warning = varianza_creciente and recuperacion_lenta
    if varianza_creciente:
        alertas.append("VARIANZA_CRECENTE")
    if recuperacion_lenta:
        alertas.append("RECUPERACION_LENTA")
    if gain >= 1.0 or early_warning:
        fallos.append(DYNAMIC_BRAKE)
        acciones.append(
            "Reducir influencia de la señal dominante y elevar confianza mínima."
        )

    # 3. Complexity, exposure and resilience constraints.
    if modules > optimal_modules or exposure > exposure_limit or resilience_value < resilience_min:
        fallos.append(MODULARIZE)
        acciones.append("Bloquear expansión y revisar modularización/exposición.")

    if MAINTENANCE in fallos:
        estado = MAINTENANCE
    elif DYNAMIC_BRAKE in fallos:
        estado = DYNAMIC_BRAKE
    elif MODULARIZE in fallos:
        estado = MODULARIZE
    else:
        estado = CONTINUE

    result = {
        "estado": estado,
        "fallos": fallos,
        "alertas": alertas,
        "acciones_recomendadas": acciones,
        "crecimiento_permitido": not fallos,
        "ejecucion_financiera_autorizada": False,
        "mantenimiento_requerido": mantenimiento_requerido,
        "metricas": {
            "reinvestment_surplus": b,
            "entropy_time_scale": t,
            "entropy_rate": entropy_rate,
            "loop_gain": gain,
            "signal_count": modules,
            "optimal_signal_count": optimal_modules,
            "exposure": exposure,
            "max_exposure": exposure_limit,
            "resilience": resilience_value,
            "minimum_resilience": resilience_min,
        },
    }
    try:
        active_key_id, _ = _fex_evidence_keyring()
        result["evidence_key_id"] = active_key_id
    except PermissionError:
        result["evidence_key_id"] = None
    result["evidence_hash"] = hash_evidencia_sostenibilidad(result)
    try:
        result["evidence_signature"] = _firma_evidencia(result)
    except PermissionError:
        result["evidence_signature"] = None
    return result
