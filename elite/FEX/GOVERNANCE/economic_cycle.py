"""Append-only, human-governed cycle for value, impact, and reinvestment proposals.

This ledger records evidence and approvals; it does not move money, place orders,
change model parameters, or claim causal impact from correlation alone.
"""

from __future__ import annotations

import json
import math
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
EVENTS = ("measure", "evaluate", "propose", "authorize", "verify", "feedback")
NEXT_EVENT = {
    "measure": "evaluate",
    "evaluate": "propose",
    "propose": "authorize",
    "authorize": "verify",
    "verify": "feedback",
}


def ledger_path() -> Path:
    return Path(
        os.environ.get(
            "CATEDRALX_IMPACT_LEDGER_PATH",
            str(Path.home() / ".local/state/chalamandra/catedralx/impact_cycle.jsonl"),
        )
    ).expanduser()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} debe ser texto no vacío.")
    return value.strip()


def _timestamp(value: Any, field: str) -> str:
    text_value = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} debe ser ISO-8601.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} debe incluir zona horaria.")
    return text_value


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{field} debe ser un número finito.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} debe ser un número finito.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} debe ser un número finito.")
    return result


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Ledger de impacto inválido en línea {line_no}."
                ) from exc
            if not isinstance(item, dict):
                raise TypeError(f"Registro de impacto inválido en línea {line_no}.")
            records.append(item)
    return records


def _append(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True)
            + "\n"
        )


def registrar_evento(
    event_type: str,
    payload: dict[str, Any],
    path: str | Path | None = None,
    *,
    cycle_id: str | None = None,
) -> str:
    """Validate and append one governed event. Each cycle advances one stage at a time."""
    kind = _text(event_type, "event_type")
    if kind not in EVENTS:
        raise ValueError("event_type debe ser uno de: " + ", ".join(EVENTS))
    if not isinstance(payload, dict):
        raise TypeError("payload debe ser un objeto.")
    target = Path(path).expanduser() if path else ledger_path()
    records = _read(target)
    identifier = _text(cycle_id, "cycle_id") if cycle_id else str(uuid.uuid4())
    existing = [row for row in records if row.get("cycle_id") == identifier]

    if kind == "measure":
        if existing:
            raise ValueError(
                "El ciclo ya existe; measure debe iniciar un cycle_id nuevo."
            )
        for field in ("metric", "source", "period", "unit", "formula"):
            _text(payload.get(field), field)
        _number(payload.get("value"), "value")
        if payload.get("target") is not None:
            _number(payload["target"], "target")
        if payload.get("uncertainty") is not None:
            uncertainty = _number(payload["uncertainty"], "uncertainty")
            if uncertainty < 0:
                raise ValueError("uncertainty no puede ser negativa.")
        _timestamp(payload.get("observed_at"), "observed_at")
    else:
        if not existing:
            raise ValueError("El ciclo no existe; primero registra measure.")
        last = existing[-1]
        expected = NEXT_EVENT.get(last["event_type"])
        if kind != expected:
            raise ValueError(
                f"Transición inválida: después de {last['event_type']} se requiere {expected}."
            )
        if kind == "evaluate":
            _text(payload.get("assessment"), "assessment")
            _text(payload.get("evidence"), "evidence")
            if payload.get("causal_claim") is True and not _text(
                payload.get("causal_method"), "causal_method"
            ):
                raise ValueError(
                    "Una afirmación causal requiere causal_method explícito."
                )
        elif kind == "propose":
            _text(payload.get("proposal"), "proposal")
            _text(payload.get("expected_outcome"), "expected_outcome")
            _text(payload.get("verification_plan"), "verification_plan")
            if "allocation_pct" in payload or "allocation_percent" in payload:
                raise ValueError(
                    "No se aceptan porcentajes de asignación arbitrarios; aporta evidencia y aprobación explícita."
                )
        elif kind == "authorize":
            _text(payload.get("approver"), "approver")
            _text(payload.get("rationale"), "rationale")
            if payload.get("approved") is not True:
                raise ValueError(
                    "authorize requiere approved=true; para rechazar, registra la decisión fuera de este ciclo aprobado."
                )
            # CX-02: no basta texto. Exige asercion firmada verificada en escritura.
            identity_assertion = payload.get("identity_assertion")
            if identity_assertion is None or identity_assertion == "" or identity_assertion == {}:
                raise PermissionError("authorize bloqueado: falta asercion firmada de identidad del aprobador")
            measure_rec = next((r for r in existing if r.get("event_type") == "measure"), None)
            measure_payload = measure_rec.get("payload") if isinstance(measure_rec, dict) else {}
            if not isinstance(measure_payload, dict):
                raise PermissionError("authorize bloqueado: measure no encontrado")
            try:
                from AEX.DECISION import ordenes
            except Exception as e:
                raise PermissionError("authorize bloqueado: no se pudo cargar verificador") from e
            verifier = ordenes.APPROVER_IDENTITY_VERIFIER
            if not callable(verifier):
                raise PermissionError("authorize bloqueado: APPROVER_IDENTITY_VERIFIER no configurado")
            prop_rec = next((r for r in existing if r.get("event_type") == "propose"), None)
            prop_payload = prop_rec.get("payload") if isinstance(prop_rec, dict) and isinstance(prop_rec.get("payload"), dict) else {}
            ctx = {"purpose": "catedralx_economic_cycle_authorization", "cycle_id": identifier, "proposal": dict(prop_payload), "measurement": dict(measure_payload)}
            try:
                _v = float(measure_payload.get("value", 0.0))
            except Exception:
                _v = 0.0
            try:
                verified = verifier(identity_assertion, ctx, _v)
            except Exception as exc:
                raise PermissionError("authorize bloqueado: firma o identidad no verificable") from exc
            if not isinstance(verified, dict) or verified.get("verified") is not True:
                raise PermissionError("authorize bloqueado: identidad no verificada")
            subj = verified.get("subject")
            perms = verified.get("permissions")
            if not isinstance(subj, str) or not subj.strip():
                raise PermissionError("authorize bloqueado: falta subject")
            if subj.strip() != _text(payload.get("approver"), "approver"):
                raise PermissionError("authorize bloqueado: approver no coincide con subject verificado")
            if not isinstance(perms, (list, tuple, set)) or "economic_cycle_authorize" not in perms:
                raise PermissionError("authorize bloqueado: falta permiso economic_cycle_authorize")
            payload = dict(payload)
            payload["identity_verified"] = True
            payload["identity_permissions"] = sorted(perms)
        elif kind == "verify":
            _text(payload.get("evidence"), "evidence")
            _text(payload.get("result"), "result")
            _timestamp(payload.get("verified_at"), "verified_at")
        elif kind == "feedback":
            _text(payload.get("lesson"), "lesson")
            _text(payload.get("next_action"), "next_action")

    event_id = str(uuid.uuid4())
    _append(
        target,
        {
            "schema_version": SCHEMA_VERSION,
            "event_id": event_id,
            "cycle_id": identifier,
            "event_type": kind,
            "recorded_at_epoch": time.time(),
            "payload": dict(payload),
            "controls": {
                "human_approval_required": kind == "authorize",
                "money_moved": False,
                "trading_enabled": False,
                "automatic_retraining": False,
            },
        },
    )
    return identifier



def cargar_propuesta_autorizada(path: str | Path, cycle_id: str) -> dict[str, Any]:
    """Load and validate one authorized proposal using the canonical economic ledger."""
    identifier = _text(cycle_id, "cycle_id")
    records = _read(Path(path).expanduser())
    events = [row for row in records if row.get("cycle_id") == identifier]
    kinds = [row.get("event_type") for row in events]
    if kinds != ["measure", "evaluate", "propose", "authorize"]:
        raise ValueError(
            "El ciclo debe contener measure → evaluate → propose → authorize, "
            "sin etapas adicionales ni omisiones"
        )
    by_type = {row["event_type"]: row.get("payload") for row in events}
    measure, evaluation, proposal, authorization = (
        by_type["measure"], by_type["evaluate"], by_type["propose"], by_type["authorize"]
    )
    if not isinstance(measure, dict):
        raise ValueError("El ciclo contiene un payload inválido")
    if not isinstance(evaluation, dict):
        raise ValueError("El ciclo contiene un payload inválido")
    if not isinstance(proposal, dict):
        raise ValueError("El ciclo contiene un payload inválido")
    if not isinstance(authorization, dict):
        raise ValueError("El ciclo contiene un payload inválido")
    if authorization.get("approved") is not True:
        raise ValueError("La propuesta no cuenta con autorización humana explícita")
    for field in ("metric", "source", "period", "unit", "formula", "observed_at"):
        _text(measure.get(field), field)
    _number(measure.get("value"), "value")
    _timestamp(measure.get("observed_at"), "observed_at")
    for field in ("assessment", "evidence"):
        _text(evaluation.get(field), field)
    for field in ("proposal", "expected_outcome", "verification_plan"):
        _text(proposal.get(field), field)
    claimed_approver = _text(authorization.get("approver"), "approver")
    _text(authorization.get("rationale"), "rationale")
    identity_assertion = authorization.get("identity_assertion")
    if identity_assertion is None or identity_assertion == "" or identity_assertion == {}:
        raise PermissionError("Despacho bloqueado: falta la aserción firmada de identidad del aprobador")

    # Validate the trust boundary here, not in the dispatcher. The injected
    # IdP verifier must validate the assertion signature and return a verified
    # immutable subject plus the explicit cycle-authorization permission.
    from AEX.DECISION import ordenes
    verifier = ordenes.APPROVER_IDENTITY_VERIFIER
    if not callable(verifier):
        raise PermissionError("Despacho bloqueado: APPROVER_IDENTITY_VERIFIER no está configurado")
    identity_context = {
        "purpose": "catedralx_economic_cycle_authorization",
        "cycle_id": identifier,
        "proposal": dict(proposal),
        "measurement": dict(measure),
    }
    try:
        verified_identity = verifier(identity_assertion, identity_context, float(measure["value"]))
    except Exception as exc:
        raise PermissionError("Despacho bloqueado: firma o identidad del aprobador no verificable") from exc
    if not isinstance(verified_identity, dict) or verified_identity.get("verified") is not True:
        raise PermissionError("Despacho bloqueado: identidad del aprobador no verificada")
    subject = verified_identity.get("subject")
    permissions = verified_identity.get("permissions")
    if not isinstance(subject, str) or not subject.strip():
        raise PermissionError("Despacho bloqueado: falta subject inmutable del aprobador")
    if subject.strip() != claimed_approver:
        raise PermissionError("Despacho bloqueado: approver no coincide con el subject verificado")
    required_permission = "economic_cycle_authorize"
    if not isinstance(permissions, (list, tuple, set)) or required_permission not in permissions:
        raise PermissionError("Despacho bloqueado: el aprobador carece de economic_cycle_authorize")
    verified_authorization = {
        key: value for key, value in authorization.items() if key != "identity_assertion"
    }
    verified_authorization.update({
        "approver": subject.strip(),
        "identity_verified": True,
        "identity_permissions": sorted(permissions),
        "identity_verification": "APPROVER_IDENTITY_VERIFIER",
    })

    return {
        "origin": "CatedralX.FEX.GOVERNANCE.economic_cycle",
        "cycle_id": identifier,
        "measurement": dict(measure),
        "assessment": dict(evaluation),
        "proposal": dict(proposal),
        "authorization": verified_authorization,
        "execution_boundary": {
            "allowed": ["analysis", "research", "candidate_generation"],
            "prohibited": [
                "publications", "external_contact", "ad_spend", "purchases",
                "financial_orders", "automatic_reinvestment",
            ],
            "independent_acceptance_required": True,
        },
    }


def resumir_ciclos(path: str | Path | None = None) -> dict[str, Any]:
    """Return a read-only summary of stages and governance controls."""
    target = Path(path).expanduser() if path else ledger_path()
    records = _read(target)
    cycles: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        identifier = record.get("cycle_id")
        if not isinstance(identifier, str):
            raise TypeError("Registro sin cycle_id válido.")
        cycles.setdefault(identifier, []).append(record)
    summary = []
    for identifier, events in cycles.items():
        kinds = [event.get("event_type") for event in events]
        # CX-02: leer flag guardado en escritura. No re-verificar aqui: quemaria nonce.
        # Ciclos viejos sin identity_verified -> False (correcto, eran acceptance-test).
        _auth_verified = any(
            e.get("event_type") == "authorize"
            and isinstance(e.get("payload"), dict)
            and e["payload"].get("identity_verified") is True
            and e["payload"].get("identity_assertion") not in (None, "", {})
            for e in events
        )
        summary.append(
            {
                "cycle_id": identifier,
                "stage": kinds[-1],
                "events": kinds,
                "complete": kinds[-1] == "feedback",
                # A ledger event records a claim; this read-only summary does
                # not perform or persist cryptographic identity verification.
                "authorization_recorded": "authorize" in kinds,
                "identity_verified": _auth_verified,
                "identity_verification_status": "verified_at_write" if _auth_verified else "not_verified",
                "human_authorized": _auth_verified,
                # Dispatch eligibility is established only by
                # cargar_propuesta_autorizada(), never by this summary.
                "dispatch_eligible": False,
                "money_moved": False,
                "trading_enabled": False,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "cycles_recorded": len(summary),
        "cycles_complete": sum(row["complete"] for row in summary),
        "cycles_pending": sum(not row["complete"] for row in summary),
        "cycles": summary,
        "read_only": True,
        "automatic_reinvestment": False,
        "automatic_retraining": False,
        "trading_enabled": False,
    }
