"""Append-only, hash-chained and Ed25519-signed target ledger.

Private keys are supplied by the caller and must be stored outside the repository.
The ledger file is an integrity-checked record, not a substitute for protected
storage, backups, or an externally anchored checkpoint.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

GENESIS_HASH = "0" * 64
LEDGER_FORMAT = "LEDGER_INMUTABLE_ENCADENADO_v1.0"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
HEX_128 = re.compile(r"^[0-9a-f]{128}$")


class LedgerError(ValueError):
    """Raised when the ledger or an append operation violates its contract."""


def _canonical_json(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LedgerError(f"Contenido no canonicalizable: {exc}") from exc
    return text.encode("utf-8")


def hash_contenido(contenido: dict[str, Any]) -> str:
    if not isinstance(contenido, dict):
        raise LedgerError("contenido debe ser un objeto JSON")
    return hashlib.sha256(_canonical_json(contenido)).hexdigest()


def hash_entrada(
    id_: str,
    timestamp: str,
    tipo: str,
    contenido_hash: str,
    hash_anterior: str,
    clave_autorizada_id: str,
) -> str:
    campos = {
        "id": id_,
        "timestamp": timestamp,
        "tipo": tipo,
        "contenido_hash": contenido_hash,
        "hash_anterior": hash_anterior,
        "clave_autorizada_id": clave_autorizada_id,
    }
    return hashlib.sha256(_canonical_json(campos)).hexdigest()


def _parse_timestamp(value: str) -> None:
    if not isinstance(value, str):
        raise LedgerError("timestamp debe ser texto RFC3339")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError("timestamp no es RFC3339 válido") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise LedgerError("timestamp debe incluir zona horaria")


def _public_key(value: Ed25519PublicKey | bytes | str) -> Ed25519PublicKey:
    if isinstance(value, Ed25519PublicKey):
        return value
    if isinstance(value, str):
        try:
            value = bytes.fromhex(value)
        except ValueError as exc:
            raise LedgerError("Clave pública no es hexadecimal") from exc
    if not isinstance(value, bytes) or len(value) != 32:
        raise LedgerError("La clave pública Ed25519 debe tener 32 bytes")
    return Ed25519PublicKey.from_public_bytes(value)


def verificar_firma(
    clave_publica: Ed25519PublicKey | bytes | str,
    entrada_hash: str,
    firma_hex: str,
) -> bool:
    if not HEX_64.fullmatch(entrada_hash) or not HEX_128.fullmatch(firma_hex):
        return False
    try:
        _public_key(clave_publica).verify(bytes.fromhex(firma_hex), entrada_hash.encode("utf-8"))
        return True
    except (InvalidSignature, LedgerError, ValueError, TypeError):
        return False


def verificar_cadena(
    ledger: dict[str, Any],
    clave_publica_por_id: Mapping[str, Ed25519PublicKey | bytes | str],
) -> tuple[bool, str, int]:
    """Verify structure, sequential IDs, hashes, signatures and terminal hash."""
    try:
        if ledger.get("formato") != LEDGER_FORMAT:
            return False, "Formato de ledger no reconocido", -1
        if ledger.get("version_esquema") != "1.0":
            return False, "Versión de esquema no reconocida", -1
        if ledger.get("hash_genesis") != GENESIS_HASH:
            return False, "Hash génesis inválido", -1
        entries = ledger.get("entradas")
        if not isinstance(entries, list):
            return False, "entradas debe ser una lista", -1

        expected_previous = GENESIS_HASH
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                return False, f"Entrada no es objeto en posición {index}", index
            expected_id = f"evt-{index + 1:07d}"
            if entry.get("id") != expected_id:
                return False, f"ID secuencial inválido; esperado {expected_id}", index
            try:
                _parse_timestamp(entry.get("timestamp"))
            except LedgerError as exc:
                return False, str(exc), index
            if not isinstance(entry.get("tipo"), str) or not entry["tipo"]:
                return False, f"tipo inválido en {expected_id}", index
            if entry.get("hash_anterior") != expected_previous:
                return False, f"Cadena rota en posición {index}: hash_anterior no coincide", index

            calculated_content = hash_contenido(entry.get("contenido"))
            if entry.get("contenido_hash") != calculated_content:
                return False, f"Contenido alterado en entrada {expected_id}", index

            key_id = entry.get("clave_autorizada_id")
            public_key = clave_publica_por_id.get(key_id) if isinstance(key_id, str) else None
            if public_key is None:
                return False, f"Clave no autorizada: {key_id}", index

            calculated_entry = hash_entrada(
                entry["id"],
                entry["timestamp"],
                entry["tipo"],
                entry["contenido_hash"],
                entry["hash_anterior"],
                key_id,
            )
            if entry.get("entrada_hash") != calculated_entry:
                return False, f"Hash de entrada inválido: {expected_id}", index
            if not verificar_firma(public_key, calculated_entry, entry.get("firma_entrada", "")):
                return False, f"Firma inválida en entrada: {expected_id}", index
            expected_previous = calculated_entry

        if ledger.get("ultimo_hash") != expected_previous:
            return False, "ultimo_hash no coincide con final de cadena", len(entries) - 1
        return True, "Cadena completa verificada", -1
    except (LedgerError, KeyError, TypeError, AttributeError) as exc:
        return False, f"Ledger inválido: {exc}", -1


@contextmanager
def _exclusive_lock(path: Path):
    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _read(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerError(f"No se pudo leer ledger: {exc}") from exc
    if not isinstance(value, dict):
        raise LedgerError("La raíz del ledger debe ser un objeto JSON")
    return value


def _atomic_write(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(ledger, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def agregar_entrada(
    ruta_ledger: str | Path,
    *,
    tipo: str,
    contenido: dict[str, Any],
    timestamp: str,
    clave_autorizada_id: str,
    clave_privada: Ed25519PrivateKey,
    claves_publicas: Mapping[str, Ed25519PublicKey | bytes | str],
) -> dict[str, Any]:
    """Append one signed event after validating the entire existing chain."""
    path = Path(ruta_ledger)
    _parse_timestamp(timestamp)
    if not isinstance(tipo, str) or not tipo:
        raise LedgerError("tipo debe ser texto no vacío")
    if not isinstance(clave_autorizada_id, str) or not clave_autorizada_id:
        raise LedgerError("clave_autorizada_id debe ser texto no vacío")
    if not isinstance(clave_privada, Ed25519PrivateKey):
        raise LedgerError("clave_privada debe ser una clave Ed25519 privada")
    if clave_autorizada_id not in claves_publicas:
        raise LedgerError("La clave de firma no está autorizada")
    if not verificar_firma(
        claves_publicas[clave_autorizada_id],
        "0" * 64,
        clave_privada.sign(("0" * 64).encode("utf-8")).hex(),
    ):
        raise LedgerError("La clave privada no corresponde a la clave pública autorizada")

    with _exclusive_lock(path):
        ledger = _read(path)
        valid, message, position = verificar_cadena(ledger, claves_publicas)
        if not valid:
            raise LedgerError(f"No se puede anexar: {message} (posición {position})")

        entries = ledger["entradas"]
        previous_hash = ledger["ultimo_hash"]
        event_id = f"evt-{len(entries) + 1:07d}"
        content_digest = hash_contenido(contenido)
        event_digest = hash_entrada(
            event_id,
            timestamp,
            tipo,
            content_digest,
            previous_hash,
            clave_autorizada_id,
        )
        signature = clave_privada.sign(event_digest.encode("utf-8")).hex()
        entry = {
            "id": event_id,
            "timestamp": timestamp,
            "tipo": tipo,
            "contenido": contenido,
            "hash_anterior": previous_hash,
            "contenido_hash": content_digest,
            "entrada_hash": event_digest,
            "firma_entrada": signature,
            "clave_autorizada_id": clave_autorizada_id,
        }
        ledger["entradas"].append(entry)
        ledger["ultimo_hash"] = event_digest

        valid, message, position = verificar_cadena(ledger, claves_publicas)
        if not valid:
            raise LedgerError(f"Fallo de verificación previo a persistencia: {message} ({position})")
        _atomic_write(path, ledger)
        return entry
