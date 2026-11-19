"""Append-only ResultStore for CatedralX (Fase 0)."""
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def default_result_store_path() -> Path:
    configured = os.environ.get("CATEDRALX_RESULT_STORE_PATH")
    candidate = (
        Path(configured).expanduser()
        if configured
        else (
            Path.home()
            / ".local"
            / "state"
            / "chalamandra"
            / "catedralx"
            / "results.jsonl"
        )
    )
    resolved = candidate.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    if resolved == repo_root or repo_root in resolved.parents:
        raise ValueError("CATEDRALX_RESULT_STORE_PATH debe estar fuera del repositorio")
    return resolved

def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _verify_contract_hash(record: dict[str, Any]) -> None:
    from .builder import verify_decision_result_hash

    if not verify_decision_result_hash(record):
        raise ValueError("DecisionResult.contract_hash ausente o inválido")


def _record_chain_hash(sequence: int, previous_hash: str, contract_hash: str, result_id: str) -> str:
    payload = {
        "sequence": sequence,
        "previous_record_hash": previous_hash,
        "contract_hash": contract_hash,
        "result_id": result_id,
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _read_verified_records(stream) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    previous_hash = "0" * 64
    expected_sequence = 1
    stream.seek(0)
    for line_number, raw_line in enumerate(stream, start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"ResultStore corrupto: JSON inválido en línea {line_number}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"ResultStore corrupto: registro no objeto en línea {line_number}")
        integrity = record.get("store_integrity")
        if not isinstance(integrity, dict):
            raise ValueError(
                f"ResultStore contiene historial legado sin cadena verificable en línea {line_number}; "
                "se requiere migración explícita"
            )
        _verify_contract_hash(record)
        sequence = integrity.get("sequence")
        previous = integrity.get("previous_record_hash")
        actual = integrity.get("record_hash")
        if (
            isinstance(sequence, bool) or not isinstance(sequence, int)
            or sequence != expected_sequence or previous != previous_hash
            or not isinstance(record.get("result_id"), str)
        ):
            raise ValueError(f"ResultStore discontinuo en línea {line_number}")
        expected = _record_chain_hash(
            sequence, previous, record["contract_hash"], record["result_id"]
        )
        if not isinstance(actual, str) or actual != expected:
            raise ValueError(f"ResultStore con hash de cadena inválido en línea {line_number}")
        records.append(record)
        previous_hash = actual
        expected_sequence += 1
    return records


def _validate_decision_result(record: dict[str, Any]) -> None:
    required = {
        "result_id", "status", "engine", "decision", "evaluation_hash", "evaluation_gate", "cycle_id",
        "evidence", "assumptions", "risks", "provenance", "trace_id", "analysis_only",
        "orders_created", "orders_executed", "contract_hash",
    }
    missing = sorted(required - set(record))
    if missing:
        raise ValueError("DecisionResult incompleto: faltan " + ", ".join(missing))
    if record.get("status") not in {"ACCEPTED", "UNCERTAIN", "REJECTED", "BLOCKED_MISSING_INPUT"}:
        raise ValueError("DecisionResult.status inválido")
    if record.get("engine") != "CatedralX":
        raise ValueError("DecisionResult.engine debe ser CatedralX")
    if record.get("decision") not in {"buy", "sell", "hold"}:
        raise ValueError("DecisionResult.decision debe ser buy, sell o hold")
    if not isinstance(record.get("evaluation_hash"), str) or not re.fullmatch(r"[0-9a-f]{64}", record["evaluation_hash"]):
        raise ValueError("DecisionResult requiere evaluation_hash SHA-256 válido")
    if record.get("evaluation_gate") not in {"ACCEPTED", "REJECTED", "BLOCKED_EVIDENCE", "BLOCKED_REINVERSION", "BLOCKED_UNCERTAINTY", "BLOCKED_DEFICIT"}:
        raise ValueError("DecisionResult.evaluation_gate inválido")
    if record["status"] == "ACCEPTED" and record["evaluation_gate"] != "ACCEPTED":
        raise ValueError("DecisionResult ACCEPTED requiere evaluation_gate ACCEPTED")
    if (
        record["status"] == "BLOCKED_MISSING_INPUT"
        and (
            record["evaluation_gate"] != "BLOCKED_UNCERTAINTY"
            or not record.get("missing_inputs")
        )
    ):
        raise ValueError("BLOCKED_MISSING_INPUT requiere gate de incertidumbre e inputs faltantes")
    trace_id = record.get("trace_id")
    if not isinstance(trace_id, str) or not re.fullmatch(r"[0-9a-f]{32}", trace_id) or trace_id == "0" * 32:
        raise ValueError("DecisionResult.trace_id debe ser un W3C trace ID válido")
    if record.get("analysis_only") is not True or record.get("orders_created") is not False or record.get("orders_executed") is not False:
        raise ValueError("DecisionResult viola los límites de ejecución")
    for key in ("evidence", "assumptions", "risks", "provenance"):
        if not isinstance(record.get(key), list):
            raise TypeError(f"DecisionResult.{key} debe ser una lista")
    if record["status"] == "ACCEPTED":
        if not record["evidence"] or not record["provenance"]:
            raise ValueError("DecisionResult ACCEPTED requiere evidencia y procedencia")
        provenance_ids = record["provenance"]
        if any(not isinstance(item, str) or not item.strip() for item in provenance_ids):
            raise ValueError("DecisionResult ACCEPTED requiere IDs de procedencia válidos")
        evidence_ids = []
        for item in record["evidence"]:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("evidence_id"), str)
                or not item["evidence_id"].strip()
                or item.get("kind") not in {"input", "observation", "calculation", "test", "external_source", "contradiction"}
                or not isinstance(item.get("digest"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", item["digest"])
                or not isinstance(item.get("source"), str)
                or not item["source"].strip()
            ):
                raise ValueError("DecisionResult ACCEPTED contiene evidencia incompleta o sin digest SHA-256")
            evidence_ids.append(item["evidence_id"])
        if len(evidence_ids) != len(set(evidence_ids)) or not set(evidence_ids).issubset(set(provenance_ids)):
            raise ValueError("DecisionResult ACCEPTED requiere IDs de evidencia únicos y enlazados a procedencia")


def append_result(record: dict[str, Any], path: str | Path | None = None) -> str:
    """Validate, chain and append a DecisionResult under an exclusive file lock."""
    if not isinstance(record, dict):
        raise TypeError("DecisionResult debe ser un objeto")
    _validate_decision_result(record)
    _verify_contract_hash(record)
    target = Path(path) if path else default_result_store_path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    result_id = record.get("result_id")
    if not isinstance(result_id, str) or not result_id.strip():
        raise ValueError("El record debe tener un 'result_id' válido")

    fd = os.open(str(target), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        with os.fdopen(fd, "r+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                existing = _read_verified_records(stream)
                if any(item.get("result_id") == result_id for item in existing):
                    raise ValueError("DecisionResult.result_id duplicado")
                previous_hash = (
                    existing[-1]["store_integrity"]["record_hash"] if existing else "0" * 64
                )
                sequence = len(existing) + 1
                record["store_integrity"] = {
                    "sequence": sequence,
                    "previous_record_hash": previous_hash,
                    "record_hash": _record_chain_hash(
                        sequence, previous_hash, record["contract_hash"], result_id
                    ),
                }
                line = json.dumps(
                    record, ensure_ascii=False, allow_nan=False, sort_keys=True
                ) + "\n"
                stream.seek(0, os.SEEK_END)
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
                os.chmod(target, 0o600)
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    return result_id


def verify_result_store(path: str | Path | None = None) -> dict[str, Any]:
    """Verify every record and chain link; corruption is reported, never skipped."""
    target = Path(path) if path else default_result_store_path()
    if not target.exists():
        return {"valid": True, "record_count": 0, "head_hash": "0" * 64}
    with target.open("r", encoding="utf-8") as stream:
        records = _read_verified_records(stream)
    head = records[-1]["store_integrity"]["record_hash"] if records else "0" * 64
    return {"valid": True, "record_count": len(records), "head_hash": head}


def get_result(result_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    """Read only after verifying the complete history; corruption fails loudly."""
    target = Path(path) if path else default_result_store_path()
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as stream:
        records = _read_verified_records(stream)
    return next((record for record in records if record.get("result_id") == result_id), None)
