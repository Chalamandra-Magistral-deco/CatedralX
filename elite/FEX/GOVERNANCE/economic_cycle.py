"""Append-only, human-governed cycle for value, impact, and reinvestment proposals.

This ledger records evidence and approvals; it does not move money, place orders,
change model parameters, or claim causal impact from correlation alone.
"""

from __future__ import annotations

import hashlib
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


def _cycle_evidence_digest(events: list[dict[str, Any]]) -> str:
    """Digest the ordered pre-authorization evidence bundle for signer binding."""
    canonical = json.dumps(
        events, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _dispatch_ledger_path() -> Path:
    return Path.home() / ".local" / "state" / "chalamandra" / "catedralx" / "dispatched_cycles.jsonl"

def _ya_despachado(cycle_id: str) -> bool:
    fp = _dispatch_ledger_path()
    if not fp.exists():
        return False
    try:
        import fcntl
        with fp.open("r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    if rec.get("cycle_id") == cycle_id and rec.get("dispatched") is True:
                        return True
                return False
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        return False

def _marcar_despachado(cycle_id: str, subject: str) -> None:
    import fcntl, os
    fp = _dispatch_ledger_path()
    fp.parent.mkdir(parents=True, exist_ok=True)
    # flock + append atomico + fsync, archivo 0600
    fd = os.open(str(fp), os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                # re-checar bajo el mismo lock, sin pedir otro lock (evita deadlock)
                f.seek(0)
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec0 = json.loads(line)
                    except Exception:
                        continue
                    if rec0.get("cycle_id") == cycle_id and rec0.get("dispatched") is True:
                        raise PermissionError(f"Despacho bloqueado: ciclo {cycle_id} ya despachado")
                f.seek(0, 2)
                rec = {"cycle_id": cycle_id, "dispatched": True, "subject": subject, "recorded_at_epoch": time.time()}
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except PermissionError:
        raise
    except Exception as e:
        raise PermissionError(f"Despacho bloqueado: no se pudo marcar despachado: {e}") from e

def _append(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True)
            + "\n"
        )


def _verify_cycle_identity(verifier, assertion, context, amount: float, *, consume_nonce: bool):
    """Verify identity; the canonical Ed25519 verifier can recheck without replay-claiming."""
    from AEX.DECISION import ordenes
    if verifier is ordenes._ed25519_approver_verifier:
        return verifier(assertion, context, amount, consume_nonce=consume_nonce)
    # Explicitly injected IdP/test verifiers keep the documented three-argument contract.
    return verifier(assertion, context, amount)


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
            ctx = {"purpose": "catedralx_economic_cycle_authorization", "cycle_id": identifier, "cycle_digest": _cycle_evidence_digest(existing), "proposal": dict(prop_payload), "measurement": dict(measure_payload)}
            try:
                _v = float(measure_payload.get("value", 0.0))
            except Exception:
                _v = 0.0
            try:
                verified = _verify_cycle_identity(verifier, identity_assertion, ctx, _v, consume_nonce=True)
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
    _auth_event = next((r for r in events if r.get("event_type") == "authorize"), None)
    _verify_at = _auth_event.get("recorded_at_epoch") if isinstance(_auth_event, dict) else None
    identity_context = {
        "purpose": "catedralx_economic_cycle_authorization",
        "cycle_id": identifier,
        "cycle_digest": _cycle_evidence_digest(events[:3]),
        "proposal": dict(proposal),
        "measurement": dict(measure),
        "verify_at": _verify_at,
    }
    try:
        verified_identity = _verify_cycle_identity(
            verifier, identity_assertion, identity_context, float(measure["value"]), consume_nonce=False
        )
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


def despachar_propuesta_autorizada(path: str | Path, cycle_id: str) -> dict[str, Any]:
    """Valida con cargar_propuesta_autorizada y marca despacho unico. Solo aqui hay merma."""
    prop = cargar_propuesta_autorizada(path, cycle_id)
    subj = prop["authorization"].get("approver", "")
    if _ya_despachado(cycle_id):
        raise PermissionError(f"Despacho bloqueado: ciclo {cycle_id} ya despachado")
    _marcar_despachado(cycle_id, subj)
    return prop

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
        # CX-02b: no confia en flag mutable. Comprueba evidencia: authorize con
        # identity_verified True + nonce reclamado en ledger de nonces para subject/cycle.
        # Solo lectura, no re-verifica firma, no gasta nonce.
        _auth_verified = False
        _auth_rec = next((e for e in events if e.get("event_type") == "authorize"), None)
        if _auth_rec is not None:
            _pay = _auth_rec.get("payload") if isinstance(_auth_rec.get("payload"), dict) else {}
            _ass = _pay.get("identity_assertion") if isinstance(_pay.get("identity_assertion"), dict) else {}
            if _pay.get("identity_verified") is True and isinstance(_ass.get("nonce"), str) and isinstance(_ass.get("subject"), str):
                try:
                    from AEX.DECISION import ordenes as _ord
                    if _ord._nonce_reclamado_ed25519(_ass["nonce"], _ass["subject"], identifier):
                        _auth_verified = True
                except Exception:
                    _auth_verified = False
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
                "identity_verification_status": "verified_at_write_nonce_claimed" if _auth_verified else "not_reverified_read_only",
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
