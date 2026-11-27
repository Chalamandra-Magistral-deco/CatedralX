"""MSX canonical provenance record builder and cycle trace aggregation.
Observation only: this module never blocks or authorizes execution.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

VALID_VECTORS = {"RSX", "SCX", "MCX", "AEX", "DSX", "MSX", "FEX"}


def calcular_hash_conjunto(contenido: Any) -> str:
    """Return SHA-256 over deterministic, strict JSON canonicalization.

    Only JSON-compatible values are accepted. Rejecting NaN and implicit
    stringification prevents different Python objects from silently sharing
    an ambiguous serialized representation.
    """
    encoded = json.dumps(
        contenido,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_provenance(name: str, module: str, version: str, inputs: Any, *,
                     output: Any = None, confidence: float | None = None,
                     status: str = "computed", vector: str = "SCX",
                     parent: str | None = None, timestamp: int | None = None) -> dict[str, Any]:
    """Emit one versioned record with deterministic input hash and explicit confidence semantics."""
    if vector not in VALID_VECTORS:
        raise ValueError(f"vector inválido: {vector}")
    if confidence is not None and (
        isinstance(confidence, bool) or not isinstance(confidence, (int, float))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        confidence = None
    encoded = json.dumps(inputs, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), default=str, allow_nan=False).encode("utf-8")
    event_time = int(timestamp if timestamp is not None else time.time())
    input_digest = hashlib.sha256(encoded).hexdigest()
    return {
        "id": f"{vector}:{module}:{event_time}:{input_digest[:16]}",
        "vector": vector, "modulo": module, "version": version,
        "timestamp": event_time,
        "input_hash": input_digest,
        # Compatibility alias for v4.2 draft consumers; canonical field is input_hash.
        "input_hash_sha256": input_digest,
        "output": output, "confidence": confidence, "parent": parent,
        "status": status,
        "confidence_status": "provided" if confidence is not None else "unavailable",
    }


def aggregate_cycle(cycle_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate already-emitted vector records without recomputing their logic."""
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id requerido")
    clean = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("cada provenance record debe ser objeto")
        if record.get("vector") not in VALID_VECTORS:
            raise ValueError("provenance record con vector inválido")
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("provenance record sin id")
        if identifier in seen:
            raise ValueError("id de provenance duplicado")
        seen.add(identifier)
        clean.append(dict(record))
    return {"cycle_id": cycle_id, "records": clean,
            "record_count": len(clean), "status": "aggregated" if clean else "no_records"}
