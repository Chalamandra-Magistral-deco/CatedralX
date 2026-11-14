"""Ed25519 approver-identity verification shared by economic cycles.

H-01 (auditoría EXPRESS 2026-11-11, corregido en la misión LIBERACIÓN):
this module used to author and persist financial orders (``generar_orden``,
``crear_token_aprobacion``, ``orden.json`` with hardcoded ``BTCUSDT``,
2 % stop-loss / 4 % take-profit and ``autorizacion_explicita/verificada:
True``). That capability was REMOVED: the canonical cycle never called it,
no production caller exists, and no consumer may treat an analysis output
as an executable order. The removal is structural, not a flag: there is no
order-writing function left in this repo to call by mistake.

What remains here, and why it was NOT deleted with the rest: the Ed25519
approver-identity verifier (``APPROVER_IDENTITY_VERIFIER``) and its nonce
ledger. ``FEX/GOVERNANCE/economic_cycle.py`` uses it to authorize economic
cycles (``economic_cycle_authorize`` permission) and to dispatch authorized
cycles — a live, approved use that has nothing to do with financial orders.
Deleting this module would have broken that authorization path, so the
order-authoring code was removed surgically and the verifier kept.

Rollback: revert the commit that removed the order functions; the code
remains in git history. No ``orden.json`` is ever written by this module.
"""

import fcntl
import json
import os
import time
from pathlib import Path

# Production must inject a trusted OIDC/IdP verifier. Never trust caller-supplied names.
# CX-01b: Verificador Ed25519 real. El worker solo conoce la PUBLIC_KEY.
# La PRIVATE_KEY nunca entra a la VM. El verificador solo verifica firma/tiempo/nonce/subject
# y devuelve permisos tal cual. Cada llamador comprueba su propio permiso:
# - ciclos economicos: economic_cycle_authorize
def _canonical_json_ed25519(obj: dict) -> bytes:
    data = {k: v for k, v in obj.items() if k != "signature"}
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _load_approver_public_key() -> bytes:
    hexkey = os.getenv("CHALAMANDRA_APPROVER_PUBLIC_KEY", "").strip()
    if not hexkey:
        raise PermissionError("APPROVER_IDENTITY_VERIFIER: CHALAMANDRA_APPROVER_PUBLIC_KEY no configurada")
    try:
        raw = bytes.fromhex(hexkey)
    except Exception as e:
        raise PermissionError("APPROVER_IDENTITY_VERIFIER: PUBLIC_KEY no es hex valido") from e
    if len(raw) != 32:
        raise PermissionError("APPROVER_IDENTITY_VERIFIER: PUBLIC_KEY debe ser 32 bytes (64 hex)")
    return raw

def _nonce_ledger_path_ed25519():
    base = os.getenv("CATEDRALX_STATE_DIR") or str(Path("~/.local/state/chalamandra/catedralx").expanduser())
    return Path(base) / "approver_nonces.jsonl"

def _reclamar_nonce_atomico(nonce: str, subject: str, cycle_id: str) -> bool:
    """Check + register nonce under ONE LOCK_EX. Devuelve False si ya existia (replay).
    Fail-closed: linea malformada -> PermissionError, no se ignora. Archivo creado con 0600.
    """
    p = _nonce_ledger_path_ed25519()
    p.parent.mkdir(parents=True, exist_ok=True)
    # os.open con 0o600: si el archivo no existe, nace con 600. Si ya existe, no cambia permisos (ver abajo).
    fd = os.open(p, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                # Endurecer permisos aunque el archivo ya existia con 660/664
                try:
                    os.chmod(p, 0o600)
                except Exception:
                    pass
                f.seek(0)
                for lineno, line in enumerate(f.read().splitlines(), 1):
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception as e:
                        raise PermissionError(f"Identidad: ledger de nonces corrupto en linea {lineno}; autorizacion bloqueada") from e
                    if not isinstance(rec, dict) or "nonce" not in rec:
                        raise PermissionError(f"Identidad: ledger de nonces corrupto en linea {lineno}: registro sin nonce")
                    if rec.get("nonce") == nonce:
                        return False
                rec = {"nonce": nonce, "subject": subject, "cycle_id": cycle_id, "used_at": int(time.time())}
                f.seek(0, 2)
                f.write(json.dumps(rec, sort_keys=True) + "\n")
                f.flush()
                return True
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except PermissionError:
        raise
    except Exception as e:
        raise PermissionError("Identidad: no se pudo reclamar nonce") from e

def _nonce_reclamado_ed25519(nonce: str, subject: str, cycle_id: str) -> bool:
    """Read-only confirmation that this exact nonce was claimed for this identity/cycle."""
    p = _nonce_ledger_path_ed25519()
    if not p.exists():
        return False
    try:
        with p.open("r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                found = False
                for lineno, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception as exc:
                        raise PermissionError(
                            f"Identidad: ledger de nonces corrupto en linea {lineno}; autorizacion bloqueada"
                        ) from exc
                    if not isinstance(rec, dict) or "nonce" not in rec:
                        raise PermissionError(
                            f"Identidad: ledger de nonces corrupto en linea {lineno}: registro sin nonce"
                        )
                    if rec.get("nonce") == nonce:
                        if rec.get("subject") != subject or rec.get("cycle_id") != cycle_id:
                            raise PermissionError("Identidad: nonce reclamado para otra identidad o ciclo")
                        found = True
                return found
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except PermissionError:
        raise
    except Exception as exc:
        raise PermissionError("Identidad: no se pudo comprobar nonce previamente reclamado") from exc


def _ed25519_approver_verifier(identity_assertion, identity_context, amount: float, *, consume_nonce: bool = True):
    if isinstance(identity_assertion, str):
        try:
            assertion = json.loads(identity_assertion)
        except Exception as e:
            raise PermissionError("Identidad: assertion no es JSON valido") from e
    elif isinstance(identity_assertion, dict):
        assertion = dict(identity_assertion)
    else:
        raise PermissionError("Identidad: assertion debe ser dict o JSON string")
    subject = assertion.get("subject")
    permissions = assertion.get("permissions")
    purpose = assertion.get("purpose")
    expected_purpose = identity_context.get("purpose") if isinstance(identity_context, dict) else None
    if expected_purpose is not None and purpose != expected_purpose:
        raise PermissionError("Identidad: purpose no coincide con contexto")
    cycle_id = assertion.get("cycle_id")
    expected_digest = identity_context.get("cycle_digest") if isinstance(identity_context, dict) else None
    if expected_digest is not None and assertion.get("cycle_digest") != expected_digest:
        raise PermissionError("Identidad: cycle_digest no coincide con evidencia del ciclo")
    iat = assertion.get("iat")
    exp = assertion.get("exp")
    nonce = assertion.get("nonce")
    signature_hex = assertion.get("signature")
    if not isinstance(subject, str) or not subject.strip():
        raise PermissionError("Identidad: falta subject")
    if not isinstance(permissions, (list, tuple)):
        raise PermissionError("Identidad: permissions debe ser lista")
    # purpose: si viene, debe ser uno de los dos conocidos. Si no viene, no lo exigimos para no romper llamadores viejos.
    if purpose is not None and purpose not in ("catedralx_economic_cycle_authorization", "catedralx_financial_order_authorization"):
        raise PermissionError("Identidad: purpose incorrecto")
    if not isinstance(nonce, str) or not nonce:
        raise PermissionError("Identidad: falta nonce")
    if not isinstance(signature_hex, str) or not signature_hex:
        raise PermissionError("Identidad: falta signature")
    # cycle_id: si el contexto tiene cycle_id, debe coincidir. Si no tiene, no lo exigimos (ordenes financieras no tienen cycle_id).
    if isinstance(identity_context, dict) and identity_context.get("cycle_id"):
        if cycle_id != identity_context["cycle_id"]:
            raise PermissionError("Identidad: cycle_id no coincide con contexto")
    # CX-02b: si el contexto trae verify_at (tiempo del authorize original),
    # verificar exp contra ese tiempo, no contra ahora. Asi un ciclo autorizado
    # hace horas sigue siendo valido para cargar/despachar. Si no viene, usar ahora.
    _verify_at = None
    if isinstance(identity_context, dict) and identity_context.get("verify_at") is not None:
        try:
            _verify_at = int(float(identity_context.get("verify_at")))
        except Exception:
            _verify_at = None
    now = _verify_at if _verify_at is not None else int(time.time())
    try:
        iat_i, exp_i = int(iat), int(exp)
    except Exception as e:
        raise PermissionError("Identidad: iat/exp no son enteros") from e
    if exp_i <= now:
        raise PermissionError("Identidad: assertion caducada")
    if iat_i > now + 60:
        raise PermissionError("Identidad: iat en futuro")
    if exp_i - iat_i > 300:
        raise PermissionError("Identidad: ventana >300s no permitida")
    # NO comprobar y registrar por separado: TOCTOU. Reclamo atomico abajo, despues de verificar firma.
    # Si lo hicieramos aqui, un replay con firma invalida quemaria el nonce. Por eso el reclamo va despues de pub.verify.
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        pub = Ed25519PublicKey.from_public_bytes(_load_approver_public_key())
        sig = bytes.fromhex(signature_hex)
        pub.verify(sig, _canonical_json_ed25519(assertion))
    except PermissionError:
        raise
    except Exception as e:
        raise PermissionError("Identidad: firma Ed25519 invalida") from e
    nonce_cycle = str(cycle_id or "")
    if consume_nonce:
        if not _reclamar_nonce_atomico(nonce, subject.strip(), nonce_cycle):
            raise PermissionError("Identidad: nonce reutilizado (replay)")
    elif not _nonce_reclamado_ed25519(nonce, subject.strip(), nonce_cycle):
        raise PermissionError("Identidad: nonce no fue reclamado en la autorización original")
    return {"verified": True, "subject": subject.strip(), "permissions": sorted(permissions)}

APPROVER_IDENTITY_VERIFIER = _ed25519_approver_verifier
