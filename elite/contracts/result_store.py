"""Append-only ResultStore for CatedralX (Fase 0)."""
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

def _validate_decision_result(record: dict[str, Any]) -> None:
    required = {
        "result_id", "status", "engine", "decision", "evaluation_hash", "evaluation_gate", "cycle_id",
        "evidence", "assumptions", "risks", "provenance", "trace_id", "analysis_only",
        "orders_created", "orders_executed",
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
    """Validate and append a DecisionResult. Invalid or untraceable decisions fail closed."""
    if not isinstance(record, dict):
        raise TypeError("DecisionResult debe ser un objeto")
    _validate_decision_result(record)
    target = Path(path) if path else default_result_store_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    result_id = record.get("result_id")
    if not isinstance(result_id, str) or not result_id.strip():
        raise ValueError("El record debe tener un 'result_id' válido")

    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n")
    return result_id

def get_result(result_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    """Read a DecisionResult by result_id. Returns None if not found."""
    target = Path(path) if path else default_result_store_path()
    if not target.exists():
        return None

    with target.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("result_id") == result_id:
                    return record
            except json.JSONDecodeError:
                continue
    return None
