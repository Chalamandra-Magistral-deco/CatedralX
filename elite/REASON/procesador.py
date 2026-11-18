"""Endocrine homeostasis processor for the reasoning layer."""
import fcntl
import hashlib
import hmac
import json
import math
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from .state_paths import canonical_state_path

RUTA_HORMONAS = canonical_state_path()

# H-03: integrity of the hormonal state. HMAC-SHA256 over the canonical
# state body, same keyring pattern as DSX guards / snapshot signing
# (versioned keyring, legacy secret fallback, keys >= 32 bytes).
# The key is intentionally separate from the snapshot and DSX keys:
# different trust domains must not share signing keys.
HORMONAS_HMAC_SECRET_ENV = "CATEDRALX_HORMONAS_HMAC_KEY"
HORMONAS_KEYRING_ENV = "CATEDRALX_HORMONAS_KEYRING"
HORMONAS_ACTIVE_KEY_ID_ENV = "CATEDRALX_HORMONAS_ACTIVE_KEY_ID"
_INTEGRITY_ALG = "HMAC-SHA256"
_MIN_KEY_BYTES = 32

PARAMS = {
    "prod_O": 0.05, "prod_D": 0.08, "prod_S": 0.06, "prod_C": 0.005,
    "prod_A": 0.03, "prod_M": 0.01, "decay_O": 0.15, "decay_D": 0.12,
    "decay_S": 0.10, "decay_C": 0.25, "decay_A": 0.20, "decay_M": 0.05,
    "alpha1": 0.3, "alpha2": 0.2, "gamma1": 0.4, "gamma2": 0.1,
    "beta1": 0.05, "beta2": 0.15, "lam": 0.1, "theta": 0.05,
}


def _s(value: Any) -> Any:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _hormonas_keyring() -> tuple[str, dict[str, bytes]]:
    """Load the hormonal-state signing keyring or fail closed."""
    raw_ring = os.environ.get(HORMONAS_KEYRING_ENV, "")
    active_id = os.environ.get(HORMONAS_ACTIVE_KEY_ID_ENV, "")
    if raw_ring:
        try:
            parsed = json.loads(raw_ring)
        except (TypeError, ValueError) as exc:
            raise PermissionError("Keyring de hormonas inválido; firma bloqueada") from exc
        if not isinstance(parsed, dict) or not active_id or active_id not in parsed:
            raise PermissionError("Keyring de hormonas sin clave activa válida; firma bloqueada")
        keys: dict[str, bytes] = {}
        for key_id, secret in parsed.items():
            if (
                not isinstance(key_id, str)
                or not key_id
                or not isinstance(secret, str)
                or len(secret.encode("utf-8")) < _MIN_KEY_BYTES
            ):
                raise PermissionError("Keyring de hormonas contiene clave inválida; firma bloqueada")
            keys[key_id] = secret.encode("utf-8")
        return active_id, keys
    legacy = os.environ.get(HORMONAS_HMAC_SECRET_ENV, "").encode("utf-8")
    if len(legacy) < _MIN_KEY_BYTES:
        raise PermissionError(
            "Firma de hormonas bloqueada: configure keyring versionado o "
            "CATEDRALX_HORMONAS_HMAC_KEY con al menos 32 bytes"
        )
    return "legacy", {"legacy": legacy}


def _sign_state(body: dict[str, Any]) -> dict[str, Any]:
    """Create a mandatory HMAC envelope; missing or invalid keys are fatal."""
    active_key_id, keys = _hormonas_keyring()
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    signature = hmac.new(keys[active_key_id], canonical, hashlib.sha256).hexdigest()
    return {"key_id": active_key_id, "alg": _INTEGRITY_ALG, "signature": signature}


def _verify_state_integrity(data: dict[str, Any]) -> None:
    """Require a valid HMAC envelope; unsigned legacy data needs explicit migration."""
    envelope = data.get("integrity")
    if envelope is None:
        raise ValueError(
            "hormonas.json: estado sin firma; ejecute migrar_estado_legacy explícitamente"
        )
    if not isinstance(envelope, dict) or envelope.get("alg") != _INTEGRITY_ALG:
        raise ValueError("hormonas.json: envelope de integridad inválido")
    key_id = envelope.get("key_id")
    signature = envelope.get("signature")
    if not isinstance(key_id, str) or not key_id or not isinstance(signature, str):
        raise ValueError("hormonas.json: envelope de integridad inválido")
    body = {key: value for key, value in data.items() if key != "integrity"}
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    try:
        _active, keys = _hormonas_keyring()
        key = keys[key_id]
    except (PermissionError, KeyError) as exc:
        raise ValueError(
            "hormonas.json: no se puede verificar la integridad (clave no disponible)"
        ) from exc
    expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    try:
        match = hmac.compare_digest(signature, expected)
    except (TypeError, ValueError):
        match = False
    if not match:
        raise ValueError("hormonas.json: integridad inválida (contenido manipulado o corrupto)")


def migrar_estado_legacy(output_path: Path | None = None) -> Path:
    """Explicitly back up and sign a validated unsigned legacy hormonal state.

    This function is never called during import or normal loading. It refuses
    already-signed files, malformed state, invalid signing configuration, and
    an existing backup. The original bytes are preserved in a sibling backup.
    """
    target = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else canonical_state_path()
    )
    try:
        original = target.read_bytes()
    except OSError as exc:
        raise ValueError(f"No se pudo leer el estado legacy: {exc}") from exc
    try:
        legacy = json.loads(original)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError("Estado legacy corrupto: no es JSON válido") from exc
    if not isinstance(legacy, dict) or "integrity" in legacy:
        raise ValueError("La migración solo acepta un objeto legacy sin campo integrity")
    concentrations = legacy.get("concentracion_actual")
    if not isinstance(concentrations, dict):
        raise ValueError("Estado legacy inválido: concentracion_actual debe ser un objeto")
    required = {
        "oxitocina_O", "dopamina_D", "serotonina_S",
        "cortisol_C", "adrenalina_A", "melatonina_M",
    }
    if not required.issubset(concentrations):
        raise ValueError("Estado legacy inválido: faltan concentraciones obligatorias")
    for name in required:
        value = concentrations[name]
        if isinstance(value, bool):
            raise ValueError(f"Estado legacy inválido: {name} no es numérico")
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Estado legacy inválido: {name} no es numérico") from exc
        if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
            raise ValueError(f"Estado legacy inválido: {name} fuera de rango")
    if not isinstance(legacy.get("contexto", {}), dict):
        raise ValueError("Estado legacy inválido: contexto debe ser un objeto")

    # Resolve signing configuration before creating the backup or changing files.
    signed = dict(legacy)
    signed["integrity"] = _sign_state(legacy)
    backup = target.with_name(target.name + ".legacy.bak")
    backup_fd = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(backup_fd, "wb") as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        backup.unlink(missing_ok=True)
        raise

    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(signed, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)
        os.chmod(target, 0o600)
        directory_fd = os.open(str(target.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return backup


class ProcesadorEndocrino:
    """Translate surprise and market dynamics into hormone concentrations."""

    def __init__(self, output_path: Path | None = None) -> None:
        self.output_path = (
            Path(output_path).expanduser().resolve()
            if output_path is not None
            else canonical_state_path()
        )
        self.conc: dict[str, float] = {
            "oxitocina_O": 0.45, "dopamina_D": 0.60, "serotonina_S": 0.50,
            "cortisol_C": 0.30, "adrenalina_A": 0.40, "melatonina_M": 0.20,
        }
        self.contexto: dict[str, Any] = {"market_phase": "desconocido", "señal_combinada": "LATERAL"}
        self._estado: dict[str, Any] = {"concentracion_actual": self.conc.copy()}
        self._cargar()

    def _cargar(self) -> None:
        # H-03: fail closed on corrupt JSON or on a present-but-invalid
        # integrity envelope, instead of silently falling back to defaults.
        # A missing file still means first run (defaults). Unsigned legacy
        # files are rejected until explicitly migrated with a preserved backup.
        try:
            raw = self.output_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ValueError(f"hormonas.json ilegible: {exc}") from exc
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(
                "hormonas.json corrupto: no es JSON válido; "
                "borre o restaure el archivo para reconstruir el estado"
            ) from exc
        if not isinstance(data, dict):
            raise ValueError("hormonas.json corrupto: el estado debe ser un objeto")
        _verify_state_integrity(data)
        try:
            loaded = data.get("concentracion_actual", {})
            if isinstance(loaded, dict):
                for name in self.conc:
                    if name in loaded:
                        self.conc[name] = float(np.clip(float(loaded[name]), 0.0, 1.0))
            if isinstance(data.get("contexto"), dict):
                self.contexto.update(data["contexto"])
            self._estado = data
        except (TypeError, ValueError) as exc:
            raise ValueError("hormonas.json corrupto: concentraciones inválidas") from exc

    def actualizar(self, inputs: dict[str, Any]) -> dict[str, float]:
        """Advance hormone concentrations by one homeostatic step."""
        sorpresa = min(abs(float(inputs.get("sorpresa", 0.0))), 2.0)
        gap = min(abs(float(inputs.get("gap", 0.0))), 0.05)
        inercia = min(abs(float(inputs.get("inercia", 0.0))), 1.0)
        cortisol = self.conc["cortisol_C"]
        self.conc["cortisol_C"] = float(np.clip(self.conc["cortisol_C"] + PARAMS["prod_C"] + PARAMS["beta1"] * sorpresa - PARAMS["decay_C"] * cortisol, 0.0, 1.0))
        self.conc["adrenalina_A"] = float(np.clip(self.conc["adrenalina_A"] + PARAMS["prod_A"] + PARAMS["beta2"] * gap + PARAMS["gamma1"] * cortisol - PARAMS["decay_A"] * self.conc["adrenalina_A"], 0.0, 1.0))
        self.conc["dopamina_D"] = float(np.clip(self.conc["dopamina_D"] + PARAMS["prod_D"] - PARAMS["alpha1"] * cortisol - PARAMS["decay_D"] * self.conc["dopamina_D"], 0.0, 1.0))
        self.conc["serotonina_S"] = float(np.clip(self.conc["serotonina_S"] + PARAMS["prod_S"] + PARAMS["lam"] * inercia - PARAMS["alpha2"] * cortisol - PARAMS["decay_S"] * self.conc["serotonina_S"], 0.0, 1.0))
        self.conc["oxitocina_O"] = float(np.clip(self.conc["oxitocina_O"] + PARAMS["prod_O"] - PARAMS["decay_O"] * self.conc["oxitocina_O"], 0.0, 1.0))
        self.conc["melatonina_M"] = float(np.clip(self.conc["melatonina_M"] + PARAMS["prod_M"] - PARAMS["decay_M"] * self.conc["melatonina_M"], 0.0, 1.0))
        return self.conc.copy()

    def guardar(self) -> dict[str, Any]:
        """Persist the current endocrine state atomically (H-03).

        Serialized with a lock file (flock), fsync of file and directory,
        0600 permissions, timezone-aware timestamp and, when a signing key
        is configured, an HMAC integrity envelope over the state body.
        """
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "concentracion_actual": {key: round(float(_s(value)), 4) for key, value in self.conc.items()},
            "estres_critico": self.conc["cortisol_C"] > 0.7,
            "contexto": self.contexto,
            "economic_feedback": getattr(self, "economic_feedback", {}),
        }
        data["integrity"] = _sign_state(data)
        self.output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = self.output_path.with_name(self.output_path.name + ".lock")
        lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=f".{self.output_path.name}.",
                    suffix=".tmp",
                    dir=str(self.output_path.parent),
                )
                temporary_path = Path(temporary_name)
                try:
                    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
                        stream.write("\n")
                        stream.flush()
                        os.fsync(stream.fileno())
                    temporary_path.replace(self.output_path)
                    os.chmod(self.output_path, 0o600)
                    directory_fd = os.open(str(self.output_path.parent), os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                except BaseException:
                    try:
                        temporary_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                    raise
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)
        self._estado = data
        return data

    def volcar_estado_quimico(self, inputs_entorno: dict[str, Any]) -> None:
        """Compatibility entry point used by the reasoning orchestrator."""
        perception = inputs_entorno.get("percepcion_espacial", {})
        self.contexto = inputs_entorno.get("contexto", self.contexto)
        self.economic_feedback = inputs_entorno.get("economic_feedback", {})
        self.actualizar({
            "sorpresa": perception.get("free_energy", 0.0),
            "gap": perception.get("gap_detectado", 0.0),
            "inercia": perception.get("inercia", 0.0),
        })
        self.guardar()

    def leer_estado_actual(self) -> dict[str, Any]:
        return self._estado


def procesar_estado_integrado(inputs_entorno: dict[str, Any]) -> dict[str, Any]:
    """Compatibility API delegated to the canonical orchestrator transducer."""
    from .orchestrator import _think_orchestrator

    transductor = _think_orchestrator.transductor
    transductor.volcar_estado_quimico(inputs_entorno)
    return transductor.leer_estado_actual()


class _LazyProcesadorEndocrino:
    """Defer legacy singleton loading until first use, never during module import."""

    def __init__(self) -> None:
        object.__setattr__(self, "_instance", None)

    def _get_instance(self) -> ProcesadorEndocrino:
        instance = object.__getattribute__(self, "_instance")
        if instance is None:
            instance = ProcesadorEndocrino()
            object.__setattr__(self, "_instance", instance)
        return instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_instance":
            object.__setattr__(self, name, value)
        else:
            setattr(self._get_instance(), name, value)


# Legacy standalone object remains available, but loading is deferred until use.
# Internal execution uses the transducer owned by the shared orchestrator.
procesador = _LazyProcesadorEndocrino()
TransductorEndocrino = ProcesadorEndocrino
