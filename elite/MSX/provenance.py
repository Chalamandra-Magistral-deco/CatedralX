"""MSX provenance records with verifiable input and cycle integrity.

MSX is observational: it records and verifies evidence but never authorizes
or executes an action. Hashes provide integrity checks, not signer identity,
authentication, or tamper-proof storage; those require separate controls.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from typing import Any

VALID_VECTORS = {"RSX", "SCX", "MCX", "AEX", "DSX", "MSX", "FEX"}
PROVENANCE_FORMAT_VERSION = 1


def _canonical_bytes(value: Any) -> bytes:
    """Serialize JSON data deterministically; reject lossy/non-finite values."""
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def calcular_hash_conjunto(contenido: Any) -> str:
    """Return SHA-256 over deterministic, strict JSON canonicalization.

    Only JSON-compatible values are accepted. Rejecting NaN and implicit
    stringification prevents different Python objects from silently sharing
    an ambiguous serialized representation.

    Public helper preserved from work/main: elite/MSX/cycle_manifest.py and
    tests/test_cycle_manifest.py import it. Same digest as _digest.
    """
    return _digest(contenido)


def _record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "record_hash"}


def build_provenance(
    name: str,
    module: str,
    version: str,
    inputs: Any,
    *,
    output: Any = None,
    confidence: float | None = None,
    status: str = "computed",
    vector: str = "SCX",
    parent: str | None = None,
    timestamp: int | None = None,
) -> dict[str, Any]:
    """Build a deterministic record bound to its canonical original inputs."""
    if vector not in VALID_VECTORS:
        raise ValueError(f"vector inválido: {vector}")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name requerido")
    if not isinstance(module, str) or not module.strip():
        raise ValueError("module requerido")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("version requerida")
    if confidence is not None and (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        confidence = None

    input_hash = _digest(inputs)
    event_time = int(timestamp if timestamp is not None else time.time())
    record = {
        "provenance_format_version": PROVENANCE_FORMAT_VERSION,
        "id": f"{vector}:{name}:{module}:{event_time}:{input_hash[:16]}",
        "name": name,
        "vector": vector,
        "modulo": module,
        "version": version,
        "timestamp": event_time,
        "input_hash_algorithm": "sha256",
        "input_hash": input_hash,
        # Compatibility alias for existing DecisionResult evidence consumers.
        "input_hash_sha256": input_hash,
        "output": output,
        "confidence": confidence,
        "parent": parent,
        "status": status,
        "confidence_status": "provided" if confidence is not None else "unavailable",
    }
    record["record_hash_algorithm"] = "sha256"
    record["record_hash"] = _digest(record)
    return record


def verify_provenance(record: Any, original_inputs: Any) -> bool:
    """Verify both the original input digest and the complete record digest."""
    if not isinstance(record, dict):
        return False
    required = {
        "provenance_format_version",
        "id",
        "name",
        "vector",
        "modulo",
        "version",
        "timestamp",
        "input_hash_algorithm",
        "input_hash",
        "record_hash_algorithm",
        "record_hash",
    }
    if not required.issubset(record):
        return False
    if record.get("provenance_format_version") != PROVENANCE_FORMAT_VERSION:
        return False
    if record.get("vector") not in VALID_VECTORS:
        return False
    if record.get("input_hash_algorithm") != "sha256":
        return False
    if record.get("record_hash_algorithm") != "sha256":
        return False
    try:
        expected_input_hash = _digest(original_inputs)
        expected_record_hash = _digest(_record_payload(record))
    except (TypeError, ValueError, OverflowError):
        return False
    if not hmac.compare_digest(str(record.get("input_hash", "")), expected_input_hash):
        return False
    if not hmac.compare_digest(str(record.get("record_hash", "")), expected_record_hash):
        return False
    expected_id = (
        f"{record['vector']}:{record['name']}:{record['modulo']}:{record['timestamp']}:"
        f"{expected_input_hash[:16]}"
    )
    return hmac.compare_digest(str(record.get("id", "")), expected_id)


def aggregate_cycle(
    cycle_id: str,
    records: list[dict[str, Any]],
    *,
    original_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify every record against original inputs and seal an ordered cycle digest.

    The caller must supply the exact original input payload for every record,
    keyed by record ID. This creates a verifiable digest manifest; it does not
    sign the manifest or persist it in immutable storage.
    """
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id requerido")
    if not isinstance(records, list):
        raise TypeError("records debe ser una lista")
    if not isinstance(original_inputs, Mapping):
        raise TypeError("original_inputs debe ser un mapping por ID de procedencia")

    clean: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("cada provenance record debe ser objeto")
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("provenance record sin id")
        if identifier in seen:
            raise ValueError("id de provenance duplicado")
        if identifier not in original_inputs:
            raise ValueError(f"faltan entradas originales para provenance: {identifier}")
        if not verify_provenance(record, original_inputs[identifier]):
            raise ValueError(f"integridad de provenance inválida: {identifier}")
        seen.add(identifier)
        clean.append(dict(record))

    extra_inputs = set(original_inputs) - seen
    if extra_inputs:
        raise ValueError("original_inputs contiene IDs que no pertenecen al ciclo")

    manifest_payload = {
        "provenance_format_version": PROVENANCE_FORMAT_VERSION,
        "cycle_id": cycle_id,
        "record_ids": [record["id"] for record in clean],
        "record_hashes": [record["record_hash"] for record in clean],
        "record_count": len(clean),
    }
    return {
        **manifest_payload,
        "records": clean,
        "cycle_hash_algorithm": "sha256",
        "cycle_hash": _digest(manifest_payload),
        "integrity_status": "verified",
        "status": "aggregated" if clean else "no_records",
    }
