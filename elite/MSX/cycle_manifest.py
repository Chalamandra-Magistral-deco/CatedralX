"""MSX cycle manifest: immutable, canonical and optionally Ed25519-signed closure record.

The manifest records a completed cycle. It does not authorize execution,
assert that source snapshots exist, or replace independent verification.
"""
from __future__ import annotations

import base64
import copy
import json
from datetime import UTC, datetime
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .provenance import calcular_hash_conjunto

SCHEMA_VERSION = "1.0"
SIGNATURE_ALGORITHM = "Ed25519"


def _utc_timestamp(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} debe ser una fecha ISO-8601 no vacía")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} no es una fecha ISO-8601 válida") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} debe incluir zona horaria")
    return parsed.astimezone(UTC).isoformat()


def _private_key(value: Ed25519PrivateKey | bytes) -> Ed25519PrivateKey:
    if isinstance(value, Ed25519PrivateKey):
        return value
    if isinstance(value, bytes):
        return Ed25519PrivateKey.from_private_bytes(value)
    raise TypeError("signing_key debe ser Ed25519PrivateKey o 32 bytes privados")


def _public_key(value: Ed25519PublicKey | bytes) -> Ed25519PublicKey:
    if isinstance(value, Ed25519PublicKey):
        return value
    if isinstance(value, bytes):
        return Ed25519PublicKey.from_public_bytes(value)
    raise TypeError("public_key debe ser Ed25519PublicKey o 32 bytes públicos")


class CicloManifest:
    """A cycle manifest whose payload and seal cannot be mutated after sealing."""

    __slots__ = ("_payload_json", "_sealed_manifest_json", "_sealed")

    def __init__(
        self,
        ciclo_id: str,
        timestamp_inicio: str,
        timestamp_cierre: str,
        snapshot_origen: str,
        conclusion_reason: str,
        intencion_aex: Mapping[str, Any],
        observacion_fex: Mapping[str, Any] | None = None,
        huellas_modulos: Mapping[str, str] | None = None,
    ) -> None:
        if not isinstance(ciclo_id, str) or not ciclo_id.strip():
            raise ValueError("ciclo_id requerido")
        if not isinstance(snapshot_origen, str):
            raise TypeError("snapshot_origen debe ser str")
        if not isinstance(conclusion_reason, str):
            raise TypeError("conclusion_reason debe ser str")
        if not isinstance(intencion_aex, Mapping):
            raise TypeError("intencion_aex debe ser un mapping")
        if observacion_fex is not None and not isinstance(observacion_fex, Mapping):
            raise TypeError("observacion_fex debe ser un mapping o None")
        if huellas_modulos is not None:
            if not isinstance(huellas_modulos, Mapping) or any(
                not isinstance(key, str) or not isinstance(value, str)
                for key, value in huellas_modulos.items()
            ):
                raise TypeError("huellas_modulos debe mapear nombres a hashes str")

        payload = {
            "schema_version": SCHEMA_VERSION,
            "ciclo_id": ciclo_id,
            "timestamp_inicio": _utc_timestamp(timestamp_inicio, "timestamp_inicio"),
            "timestamp_cierre": _utc_timestamp(timestamp_cierre, "timestamp_cierre"),
            "snapshot_origen": snapshot_origen,
            "conclusion_reason": conclusion_reason,
            "intencion_aex": copy.deepcopy(dict(intencion_aex)),
            "observacion_fex": copy.deepcopy(dict(observacion_fex)) if observacion_fex is not None else None,
            "huellas_modulos": copy.deepcopy(dict(huellas_modulos or {})),
        }
        # Keep canonical JSON text, not a mutable dict, as the internal source of truth.
        self._payload_json = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
        self._sealed_manifest_json = None
        self._sealed = False

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("el manifiesto está sellado y no admite modificaciones")
        object.__setattr__(self, name, value)

    @property
    def ciclo_id(self) -> str:
        return json.loads(self._payload_json)["ciclo_id"]

    @property
    def timestamp_inicio(self) -> str:
        return json.loads(self._payload_json)["timestamp_inicio"]

    @property
    def timestamp_cierre(self) -> str:
        return json.loads(self._payload_json)["timestamp_cierre"]

    def generar_manifest(self) -> dict[str, Any]:
        """Return a detached copy of the unsigned manifest payload."""
        return json.loads(self._payload_json)

    def hash_final(self) -> str:
        """Calculate the SHA-256 digest of the canonical payload."""
        return calcular_hash_conjunto(json.loads(self._payload_json))

    def sellar(
        self,
        signing_key: Ed25519PrivateKey | bytes | None = None,
        *,
        key_id: str | None = None,
    ) -> dict[str, Any]:
        """Seal once; optionally sign the digest with an externally managed Ed25519 key.

        No private key is read from disk or stored in the repository. Without a
        key, the result is explicitly marked UNSIGNED and must not be treated as
        an authenticated closure.
        """
        if self._sealed:
            return json.loads(self._sealed_manifest_json)

        digest = self.hash_final()
        complete = self.generar_manifest()
        complete["hash_integridad"] = digest
        complete["hash_algorithm"] = "SHA-256"
        complete["canonicalization"] = "JSON-sort-keys-UTF8-compact-v1"
        complete["sellado_utc"] = datetime.now(UTC).isoformat()

        if signing_key is None:
            if key_id is not None:
                raise ValueError("key_id no se admite sin signing_key")
            complete["signature"] = None
            complete["signature_status"] = "UNSIGNED"
        else:
            if not isinstance(key_id, str) or not key_id.strip():
                raise ValueError("key_id requerido para identificar la clave de firma")
            signer = _private_key(signing_key)
            signature = signer.sign(digest.encode("ascii"))
            complete["signature"] = {
                "algorithm": SIGNATURE_ALGORITHM,
                "key_id": key_id,
                "value_base64": base64.b64encode(signature).decode("ascii"),
            }
            complete["signature_status"] = "SIGNED"

        # Store a detached snapshot before freezing the object.
        object.__setattr__(
            self,
            "_sealed_manifest_json",
            json.dumps(complete, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        )
        object.__setattr__(self, "_sealed", True)
        return json.loads(self._sealed_manifest_json)


def verificar_firma_manifest(
    manifest: Mapping[str, Any],
    public_key: Ed25519PublicKey | bytes,
) -> bool:
    """Verify the Ed25519 signature and canonical payload digest.

    The public key must come from a trusted external key registry. This
    function does not establish trust in key_id or validate snapshot existence.
    """
    if not isinstance(manifest, Mapping):
        raise TypeError("manifest debe ser un mapping")
    signature_record = manifest.get("signature")
    if not isinstance(signature_record, Mapping):
        return False
    if signature_record.get("algorithm") != SIGNATURE_ALGORITHM:
        return False
    digest = manifest.get("hash_integridad")
    if not isinstance(digest, str) or len(digest) != 64:
        return False

    payload = {
        key: copy.deepcopy(value)
        for key, value in manifest.items()
        if key not in {
            "hash_integridad", "hash_algorithm", "canonicalization",
            "sellado_utc", "signature", "signature_status",
        }
    }
    if calcular_hash_conjunto(payload) != digest:
        return False
    try:
        signature = base64.b64decode(signature_record["value_base64"], validate=True)
        _public_key(public_key).verify(signature, digest.encode("ascii"))
    except (KeyError, ValueError, TypeError, InvalidSignature):
        return False
    return manifest.get("signature_status") == "SIGNED"


def construir_manifiesto_desde_ciclo(
    ciclo_id: str,
    datos_ciclo: Mapping[str, Any],
    *,
    timestamp_cierre: str | None = None,
) -> CicloManifest:
    """Build a manifest from completed cycle data without inventing missing start time."""
    if not isinstance(datos_ciclo, Mapping):
        raise TypeError("datos_ciclo debe ser un mapping")
    inicio = datos_ciclo.get("timestamp_inicio")
    cierre = timestamp_cierre or datos_ciclo.get("timestamp_cierre") or datetime.now(UTC).isoformat()
    if not isinstance(inicio, str) or not inicio.strip():
        raise ValueError("datos_ciclo.timestamp_inicio es obligatorio")
    intencion = datos_ciclo.get("intencion", {})
    if not isinstance(intencion, Mapping):
        raise TypeError("datos_ciclo.intencion debe ser un mapping")
    observacion = datos_ciclo.get("observacion_fex")
    huellas = datos_ciclo.get("huellas", {})
    return CicloManifest(
        ciclo_id=ciclo_id,
        timestamp_inicio=inicio,
        timestamp_cierre=cierre,
        snapshot_origen=datos_ciclo.get("snapshot_hash", ""),
        conclusion_reason=datos_ciclo.get("conclusion", ""),
        intencion_aex=intencion,
        observacion_fex=observacion,
        huellas_modulos=huellas,
    )
