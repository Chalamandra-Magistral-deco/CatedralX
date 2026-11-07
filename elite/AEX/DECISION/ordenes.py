"""Build pending orders only after authenticated, one-time approval and safety checks."""

import fcntl
import hashlib
import hmac
import json
import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from DSX.DEFENSE import defense
from DSX.DEFENSE.guards import verificar_autorizacion_ejecucion

BASE_STATE = Path(os.environ.get("CATEDRALX_STATE_DIR", "~/.local/state/chalamandra/catedralx")).expanduser()
COMMAND_OUTPUT = Path(os.environ.get("CATEDRALX_OUTPUT", str(BASE_STATE / "orden.json"))).expanduser()
APPROVAL_DIR = Path(os.environ.get("CATEDRALX_APPROVAL_DIR", str(COMMAND_OUTPUT.parent / "approvals"))).expanduser()
APPROVAL_TTL_SECONDS = 120
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
_ACTIVE_ACTIONS = {"ENTRAR_LARGO", "ENTRAR_CORTO"}
# Production must inject a trusted OIDC/IdP verifier. Never trust caller-supplied names.
# CX-01b: Verificador Ed25519 real. El worker solo conoce la PUBLIC_KEY.
# La PRIVATE_KEY nunca entra a la VM. El verificador solo verifica firma/tiempo/nonce/subject
# y devuelve permisos tal cual. Cada llamador comprueba su propio permiso:
# - ordenes financieras: financial_order_approve
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

def _nonce_usado_ed25519(nonce: str) -> bool:
    # Legacy: solo lectura. NO usar para decision de replay. Usar _reclamar_nonce_atomico.
    p = _nonce_ledger_path_ed25519()
    if not p.exists():
        return False
    for line in p.read_text(errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            if json.loads(line).get("nonce") == nonce:
                return True
        except Exception:
            continue
    return False

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


def _registrar_nonce_ed25519(nonce: str, subject: str, cycle_id: str) -> None:
    # Legacy wrapper: delega a atomico, ignora replay (para compatibilidad con llamadores viejos)
    _reclamar_nonce_atomico(nonce, subject, cycle_id)

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
_REQUIRED_APPROVAL_PERMISSION = "financial_order_approve"


def verificar_identidad_aprobador(identity_assertion: Any, decision: dict[str, Any], precio_actual: float) -> dict[str, Any]:
    """Validate an assertion through a trusted external identity provider; deny by default."""
    verifier = APPROVER_IDENTITY_VERIFIER
    if not callable(verifier):
        raise PermissionError("Aprobación bloqueada: verificador externo de identidad no configurado")
    try:
        identity = verifier(identity_assertion, decision, float(precio_actual))
    except Exception as exc:
        raise PermissionError("Aprobación bloqueada: no se pudo verificar la identidad externa") from exc
    if not isinstance(identity, dict) or identity.get("verified") is not True:
        raise PermissionError("Aprobación bloqueada: identidad externa no verificada")
    subject = identity.get("subject")
    permissions = identity.get("permissions")
    if not isinstance(subject, str) or not subject.strip():
        raise PermissionError("Aprobación bloqueada: falta el identificador inmutable del aprobador")
    if not isinstance(permissions, (list, tuple, set)) or _REQUIRED_APPROVAL_PERMISSION not in permissions:
        raise PermissionError("Aprobación bloqueada: el aprobador no tiene el permiso requerido")
    return {"subject": subject.strip(), "permissions": sorted(permissions)}


APPROVAL_ACTIVE_KEY_ID_ENV = "CATEDRALX_APPROVAL_ACTIVE_KEY_ID"
APPROVAL_KEYRING_ENV = "CATEDRALX_APPROVAL_KEYRING"


def _approval_keyring() -> tuple[str, dict[str, bytes]]:
    """Load a versioned approval keyring; active key signs and overlap keys verify."""
    raw_ring = os.environ.get(APPROVAL_KEYRING_ENV, "")
    active_id = os.environ.get(APPROVAL_ACTIVE_KEY_ID_ENV, "")
    if raw_ring:
        try:
            parsed = json.loads(raw_ring)
        except (TypeError, ValueError) as exc:
            raise PermissionError("Keyring de aprobación inválido; autorización bloqueada") from exc
        if not isinstance(parsed, dict) or not active_id or active_id not in parsed:
            raise PermissionError("Keyring de aprobación sin clave activa válida; autorización bloqueada")
        keys = {}
        for key_id, secret in parsed.items():
            if not isinstance(key_id, str) or not key_id or not isinstance(secret, str) or len(secret.encode("utf-8")) < 32:
                raise PermissionError("Keyring de aprobación contiene clave inválida; autorización bloqueada")
            keys[key_id] = secret.encode("utf-8")
        return active_id, keys
    legacy = os.environ.get("CATEDRALX_APPROVAL_SECRET", "").encode("utf-8")
    if len(legacy) < 32:
        raise PermissionError("Autorización bloqueada: configure keyring versionado o CATEDRALX_APPROVAL_SECRET con al menos 32 bytes")
    return "legacy", {"legacy": legacy}


def _approval_key(key_id: str | None = None) -> bytes:
    active_id, keys = _approval_keyring()
    selected = active_id if key_id is None else key_id
    if selected not in keys:
        raise PermissionError("Clave de aprobación desconocida o retirada; autorización bloqueada")
    return keys[selected]


def crear_token_aprobacion(decision: dict[str, Any], precio_actual: float, *, identity_assertion: Any, emitido_en: int | None = None) -> str:
    """Create a signed approval only after trusted external identity and permission checks."""
    identity = verificar_identidad_aprobador(identity_assertion, decision, precio_actual)
    active_key_id, _ = _approval_keyring()
    key = _approval_key(active_key_id)
    payload = {
        "key_id": active_key_id,
        "aprobador": identity["subject"],
        "permisos_verificados": identity["permissions"],
        "emitido_en": int(time.time()) if emitido_en is None else int(emitido_en),
        "accion": str(decision.get("accion", "")),
        "precio_actual": float(precio_actual),
        "tamano": float(decision.get("tamano", 0.0)),
        "confianza": float(decision.get("confianza", 0.0)),
        "razon_hash": hashlib.sha256(str(decision.get("razon", "")).encode("utf-8")).hexdigest(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    signature = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    return json.dumps({"payload": payload, "signature": signature}, sort_keys=True, separators=(",", ":"))


def _consumir_token_aprobacion(token: str, decision: dict[str, Any], precio_actual: float) -> str:
    """Verify a signed approval token, bind it to this exact order, and consume it once."""
    try:
        envelope = json.loads(token)
        payload = envelope["payload"]
        signature = envelope["signature"]
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise PermissionError("Token de autorización inválido") from exc
    key_id = payload.get("key_id")
    key = _approval_key(key_id if isinstance(key_id, str) else None)
    expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        raise PermissionError("Firma de autorización inválida")
    now = int(time.time())
    issued = payload.get("emitido_en")
    if not isinstance(issued, int) or issued > now + 5 or now - issued > APPROVAL_TTL_SECONDS:
        raise PermissionError("Autorización caducada o con fecha inválida")
    expected_fields = {
        "accion": str(decision.get("accion", "")),
        "precio_actual": float(precio_actual),
        "tamano": float(decision.get("tamano", 0.0)),
        "confianza": float(decision.get("confianza", 0.0)),
        "razon_hash": hashlib.sha256(str(decision.get("razon", "")).encode("utf-8")).hexdigest(),
    }
    if any(payload.get(name) != value for name, value in expected_fields.items()):
        raise PermissionError("La aprobación no corresponde exactamente a esta orden")
    approver = payload.get("aprobador")
    if not isinstance(approver, str) or not approver.strip():
        raise PermissionError("Identidad del aprobador ausente")
    token_id = hashlib.sha256(token.encode("utf-8")).hexdigest()
    approval_dir = Path(APPROVAL_DIR).expanduser()
    try:
        approval_dir.mkdir(parents=True, exist_ok=True)
        consumed = approval_dir / f"{token_id}.used"
        fd = os.open(str(consumed), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as marker:
            marker.write(f"{approver}\n{now}\n")
    except FileExistsError as exc:
        # Recovery is allowed only while the caller holds the generation lock,
        # the canonical order is still absent, and the existing marker matches
        # this exact signed token's approver and a fresh consumption timestamp.
        try:
            marker_data = consumed.read_text(encoding="utf-8").splitlines()
            marker_time = int(marker_data[1]) if len(marker_data) == 2 else -1
            order = _cargar_orden_idempotente(token)
            if (order is None and marker_data[0] == approver
                    and marker_time > 0 and now - marker_time <= APPROVAL_TTL_SECONDS):
                return approver
        except (OSError, ValueError, IndexError):
            pass
        raise PermissionError("Esta autorización ya fue utilizada o no es recuperable") from exc
    except OSError as exc:
        raise PermissionError("No se pudo registrar el consumo de autorización; operación bloqueada") from exc
    return approver


def _hash_token_aprobacion(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _cargar_orden_idempotente(token: str) -> dict[str, Any] | None:
    """Return the already-persisted order for this exact approval, if present."""
    if not COMMAND_OUTPUT.is_file():
        return None
    try:
        existing = json.loads(COMMAND_OUTPUT.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise PermissionError("Persistencia de orden inconsistente; creación bloqueada para recuperación") from exc
    if not isinstance(existing, dict):
        raise PermissionError("Persistencia de orden inválida; creación bloqueada para recuperación")
    if existing.get("approval_token_hash") == _hash_token_aprobacion(token):
        return existing
    return None


def _escribir_atomico(path: Path, content: str) -> None:
    """Write and fsync a temporary file before atomically replacing the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def recuperar_memoria_desde_orden() -> bool:
    """Rebuild a missing history entry from the canonical pending-order file."""
    if not COMMAND_OUTPUT.is_file():
        return False
    try:
        order = json.loads(COMMAND_OUTPUT.read_text(encoding="utf-8"))
        if not isinstance(order, dict) or not isinstance(order.get("approval_token_hash"), str):
            return False
        history_path = COMMAND_OUTPUT.with_name("decisiones.jsonl")
        if history_path.is_file():
            for line in history_path.read_text(encoding="utf-8").splitlines():
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("approval_token_hash") == order["approval_token_hash"]:
                    return True
        record = {"timestamp": order.get("timestamp"), "accion": order.get("accion"),
                  "confianza": order.get("confianza"), "razon": order.get("motivo", ""),
                  "approval_token_hash": order["approval_token_hash"]}
        with history_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return True
    except (OSError, TypeError, ValueError):
        return False


def _guardar_memoria(decision: dict[str, Any]) -> None:
    """Persist a compact decision history without requiring another module."""
    history_path = COMMAND_OUTPUT.with_name("decisiones.jsonl")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as history_file:
        history_file.write(json.dumps({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "accion": decision["accion"],
            "confianza": decision["confianza"],
            "razon": decision.get("razon", ""),
            "approval_token_hash": decision.get("approval_token_hash"),
        }, ensure_ascii=False, allow_nan=False) + "\n")
        history_file.flush()
        os.fsync(history_file.fileno())


def _generar_orden_bajo_bloqueo(
    decision: dict[str, Any],
    precio_actual: float,
    *,
    token_aprobacion: str | None = None,
    autorizacion_explicita: bool = False,
    dsx_authorization: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Persist a pending order only with signed, fresh, one-time approval and safe state."""
    # Legacy boolean deliberately does not grant permission.
    if not token_aprobacion:
        raise PermissionError("Se requiere token_aprobacion firmado; un booleano no autoriza")
    accion = decision.get("accion")
    if accion == "ESPERAR":
        return None
    if accion not in _ACTIVE_ACTIONS:
        raise ValueError(f"Acción no soportada: {accion!r}")
    try:
        precio = float(precio_actual)
        tamano = float(decision.get("tamano", 0.0))
        confianza = float(decision.get("confianza", 0.0))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("precio, tamano y confianza deben ser numericos validos") from exc
    if not math.isfinite(precio) or precio <= 0.0:
        raise ValueError("precio_actual debe ser finito y positivo")
    if not math.isfinite(tamano) or tamano <= 0.0:
        raise ValueError("tamano debe ser finito y positivo")
    if not math.isfinite(confianza) or not 0.0 <= confianza <= 1.0:
        raise ValueError("confianza debe ser finita y estar entre 0 y 1")

    panic_path = Path(defense.PATH_PANIC).expanduser()
    if not panic_path.parent.is_dir():
        raise PermissionError("Ubicación del bloqueo de emergencia no disponible: se bloquea la creación de órdenes")
    if panic_path.exists():
        raise PermissionError("Bloqueo de emergencia activo: no se puede crear una orden")

    # A signed human approval is necessary but not sufficient: DSX must also
    # provide a passing governance result. This is a software gate, not a live
    # execution authorization.
    if not isinstance(dsx_authorization, dict):
        raise PermissionError("Bloqueo DSX: se requiere resultado de gobernanza válido")
    if (dsx_authorization.get("enforcement_vector") != "DSX"
            or dsx_authorization.get("allowed") is not True
            or dsx_authorization.get("blocked") is not False
            or dsx_authorization.get("governance_status") != "verified"
            or dsx_authorization.get("governance_metrics_complete") is not True
            or dsx_authorization.get("financial_execution_authorized") is not False):
        raise PermissionError("Bloqueo DSX: gobernanza ausente, bloqueada o inválida")
    if not verificar_autorizacion_ejecucion(dsx_authorization, decision, precio):
        raise PermissionError("Bloqueo DSX: autorización firmada ausente, caducada, falsificada o no corresponde a esta orden")

    recovered = _cargar_orden_idempotente(token_aprobacion)
    if recovered is not None:
        return recovered
    approver = _consumir_token_aprobacion(token_aprobacion, decision, precio)
    # Recheck emergency state after consuming approval to fail closed on races.
    if not panic_path.parent.is_dir() or panic_path.exists():
        raise PermissionError("Bloqueo de emergencia activo o no disponible")

    if accion == "ENTRAR_LARGO":
        stop_loss = round(precio * (1.0 - STOP_LOSS_PCT), 2)
        take_profit = round(precio * (1.0 + TAKE_PROFIT_PCT), 2)
    else:
        stop_loss = round(precio * (1.0 + STOP_LOSS_PCT), 2)
        take_profit = round(precio * (1.0 - TAKE_PROFIT_PCT), 2)
    orden = {
        "id": int(time.time() * 1000), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "approval_token_hash": _hash_token_aprobacion(token_aprobacion),
        "activo": "BTCUSDT", "accion": accion, "tamano": tamano,
        "precio_referencia": precio, "stop_loss": stop_loss, "take_profit": take_profit,
        "confianza": confianza, "motivo": str(decision.get("razon", "")),
        "estado": "PENDIENTE", "autorizacion_explicita": True,
        "aprobador": approver, "autorizacion_verificada": True,
        "dsx_governance_status": dsx_authorization.get("governance_status", "unknown"),
        "dsx_financial_execution_authorized": False,
    }
    _escribir_atomico(COMMAND_OUTPUT, json.dumps(orden, indent=2, ensure_ascii=False, allow_nan=False))
    _guardar_memoria({**decision, "confianza": confianza, "approval_token_hash": orden["approval_token_hash"]})
    return orden


def generar_orden(
    decision: dict[str, Any],
    precio_actual: float,
    *,
    token_aprobacion: str | None = None,
    autorizacion_explicita: bool = False,
    dsx_authorization: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Serialize order recovery/persistence so a crash can be retried safely."""
    if not token_aprobacion:
        raise PermissionError("Se requiere token_aprobacion firmado; un booleano no autoriza")
    lock_dir = Path(APPROVAL_DIR).expanduser()
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / ".order-generation.lock"
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        with os.fdopen(fd, "r+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                return _generar_orden_bajo_bloqueo(
                    decision, precio_actual, token_aprobacion=token_aprobacion,
                    autorizacion_explicita=autorizacion_explicita,
                    dsx_authorization=dsx_authorization,
                )
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except Exception:
        # fdopen owns fd after success; if fdopen itself fails, close best-effort.
        raise
