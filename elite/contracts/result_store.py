"""Append-only ResultStore for DecisionResult and economic-opportunity results."""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TRACE_RE = re.compile(r"^[0-9a-f]{32}$")
_DECISIONS = {"PURSUE", "DEFER", "REJECT"}
_SCENARIOS = {"conservative", "base", "optimistic"}


def default_result_store_path() -> Path:
    configured = os.environ.get("CATEDRALX_RESULT_STORE_PATH")
    candidate = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".local" / "state" / "chalamandra" / "catedralx" / "results.jsonl"
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
    optional = {"tests", "next_action", "missing_inputs", "blocking_reasons", "evaluation_reason"}
    allowed = required | optional
    missing = sorted(required - set(record))
    if missing:
        raise ValueError("DecisionResult incompleto: faltan " + ", ".join(missing))
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise ValueError("DecisionResult contiene propiedades no permitidas: " + ", ".join(unknown))
    if not isinstance(record["result_id"], str) or not record["result_id"].strip():
        raise ValueError("DecisionResult.result_id debe ser texto no vacío")
    if record.get("status") not in {"ACCEPTED", "UNCERTAIN", "REJECTED", "BLOCKED_MISSING_INPUT"}:
        raise ValueError("DecisionResult.status inválido")
    if record.get("engine") != "CatedralX":
        raise ValueError("DecisionResult.engine debe ser CatedralX")
    if record.get("decision") not in {"buy", "sell", "hold"}:
        raise ValueError("DecisionResult.decision debe ser buy, sell o hold")
    if not isinstance(record.get("evaluation_hash"), str) or not _SHA256_RE.fullmatch(record["evaluation_hash"]):
        raise ValueError("DecisionResult requiere evaluation_hash SHA-256 válido")
    if record.get("evaluation_gate") not in {"ACCEPTED", "REJECTED", "BLOCKED_EVIDENCE", "BLOCKED_REINVERSION", "BLOCKED_UNCERTAINTY", "BLOCKED_DEFICIT"}:
        raise ValueError("DecisionResult.evaluation_gate inválido")
    if record["status"] == "ACCEPTED" and record["evaluation_gate"] != "ACCEPTED":
        raise ValueError("DecisionResult ACCEPTED requiere evaluation_gate ACCEPTED")
    if record["status"] == "BLOCKED_MISSING_INPUT" and (
        record["evaluation_gate"] != "BLOCKED_UNCERTAINTY" or not record.get("missing_inputs")
    ):
        raise ValueError("BLOCKED_MISSING_INPUT requiere gate de incertidumbre e inputs faltantes")
    if record["cycle_id"] is not None and type(record["cycle_id"]) not in {str, int}:
        raise ValueError("DecisionResult.cycle_id debe ser string, integer o null")
    trace_id = record.get("trace_id")
    if not isinstance(trace_id, str) or not _TRACE_RE.fullmatch(trace_id) or trace_id == "0" * 32:
        raise ValueError("DecisionResult.trace_id debe ser un W3C trace ID válido")
    if record.get("analysis_only") is not True or record.get("orders_created") is not False or record.get("orders_executed") is not False:
        raise ValueError("DecisionResult viola los límites de ejecución")
    for key in ("evidence", "assumptions", "risks", "provenance"):
        if not isinstance(record.get(key), list):
            raise TypeError(f"DecisionResult.{key} debe ser una lista")
    for key in ("assumptions", "risks", "provenance"):
        if any(not isinstance(item, str) for item in record[key]):
            raise TypeError(f"DecisionResult.{key} solo admite texto")
    for key in ("tests", "missing_inputs", "blocking_reasons"):
        if key in record and (
            not isinstance(record[key], list) or any(not isinstance(item, str) for item in record[key])
        ):
            raise TypeError(f"DecisionResult.{key} debe ser una lista de texto")
    if "next_action" in record and not isinstance(record["next_action"], str):
        raise TypeError("DecisionResult.next_action debe ser texto")
    if "evaluation_reason" in record and record["evaluation_reason"] is not None and not isinstance(record["evaluation_reason"], str):
        raise TypeError("DecisionResult.evaluation_reason debe ser texto o null")
    if any(not isinstance(item, dict) for item in record["evidence"]):
        raise TypeError("DecisionResult.evidence debe contener objetos")
    if record["status"] == "ACCEPTED":
        if not record["evidence"] or not record["provenance"]:
            raise ValueError("DecisionResult ACCEPTED requiere evidencia y procedencia")
        provenance_ids = record["provenance"]
        if any(not item.strip() for item in provenance_ids):
            raise ValueError("DecisionResult ACCEPTED requiere IDs de procedencia válidos")
        evidence_ids = []
        for item in record["evidence"]:
            if (
                not isinstance(item.get("evidence_id"), str)
                or not item["evidence_id"].strip()
                or item.get("kind") not in {"input", "observation", "calculation", "test", "external_source", "contradiction"}
                or not isinstance(item.get("digest"), str)
                or not _SHA256_RE.fullmatch(item["digest"])
                or not isinstance(item.get("source"), str)
                or not item["source"].strip()
            ):
                raise ValueError("DecisionResult ACCEPTED contiene evidencia incompleta o sin digest SHA-256")
            evidence_ids.append(item["evidence_id"])
        if len(evidence_ids) != len(set(evidence_ids)) or not set(evidence_ids).issubset(set(provenance_ids)):
            raise ValueError("DecisionResult ACCEPTED requiere IDs de evidencia únicos y enlazados a procedencia")


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _aware_timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field} debe ser una fecha ISO-8601 con zona horaria")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} debe ser una fecha ISO-8601 válida") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} debe incluir zona horaria")


def _opportunity_hash(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "evaluation_hash"}
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False, default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_economic_opportunity_result(record: dict[str, Any]) -> None:
    required = {
        "schema_version", "result_id", "engine", "evaluation_domain", "status", "opportunity_id",
        "income_model", "currency", "horizon_months", "financials", "scenarios", "decision_candidate",
        "risk_flags", "assumptions", "evidence", "evidence_status", "uncertainty", "provenance",
        "trace_id", "evaluation_hash", "analysis_only", "orders_created", "orders_executed",
        "authorization", "independent_acceptance_required",
    }
    missing = sorted(required - set(record))
    if missing:
        raise ValueError("EconomicOpportunityResult incompleto: faltan " + ", ".join(missing))
    if record["schema_version"] != "catedralx.economic-opportunity/1.0":
        raise ValueError("schema_version económico inválido")
    if record["engine"] != "CatedralX" or record["evaluation_domain"] != "business_opportunity":
        raise ValueError("engine/evaluation_domain económicos inválidos")
    if record["status"] != "ANALYSIS_COMPLETE":
        raise ValueError("EconomicOpportunityResult.status debe ser ANALYSIS_COMPLETE")
    if not isinstance(record["result_id"], str) or not _TRACE_RE.fullmatch(record["result_id"]):
        raise ValueError("result_id debe contener 32 caracteres hexadecimales")
    if not isinstance(record["opportunity_id"], str) or not record["opportunity_id"].strip():
        raise ValueError("opportunity_id requerido")
    if record["income_model"] not in {"active", "passive", "hybrid", "investment", "asset"}:
        raise ValueError("income_model inválido")
    if not isinstance(record["currency"], str) or not re.fullmatch(r"[A-Z]{3}", record["currency"]):
        raise ValueError("currency debe ser un código ISO-4217 de tres letras")
    if type(record["horizon_months"]) is not int or not 1 <= record["horizon_months"] <= 120:
        raise ValueError("horizon_months debe ser entero entre 1 y 120")
    trace_id = record["trace_id"]
    if not isinstance(trace_id, str) or not _TRACE_RE.fullmatch(trace_id) or trace_id == "0" * 32:
        raise ValueError("trace_id W3C inválido")

    financials = record["financials"]
    financial_required = {
        "capital_required", "available_capital", "funding_gap", "revenue_total_base_input",
        "cost_total_base_input", "initial_capital_status", "working_capital_assessment", "tax_assessment",
    }
    if not isinstance(financials, dict) or financial_required - set(financials):
        raise ValueError("financials incompleto")
    if set(financials) - financial_required:
        raise ValueError("financials contiene propiedades no permitidas")
    for field in ("capital_required", "available_capital", "funding_gap", "revenue_total_base_input", "cost_total_base_input"):
        if not _finite_number(financials[field]) or financials[field] < 0:
            raise ValueError(f"financials.{field} debe ser finito y no negativo")
    expected_gap = max(0.0, float(financials["capital_required"]) - float(financials["available_capital"]))
    if not math.isclose(float(financials["funding_gap"]), expected_gap, rel_tol=0, abs_tol=0.011):
        raise ValueError("financials.funding_gap no coincide con capital requerido menos capital disponible")
    expected_status = "funded" if expected_gap == 0 else "funding_gap"
    if financials["initial_capital_status"] != expected_status:
        raise ValueError("financials.initial_capital_status inconsistente")
    if financials["working_capital_assessment"] != "not_assessed_without_periodic_cashflow":
        raise ValueError("working_capital_assessment inválido")
    if financials["tax_assessment"] != "not_included_unless_declared_as_cost_line":
        raise ValueError("tax_assessment inválido")

    scenarios = record["scenarios"]
    if not isinstance(scenarios, dict) or set(scenarios) != _SCENARIOS:
        raise ValueError("scenarios debe contener conservative, base y optimistic")
    for name, scenario in scenarios.items():
        fields = {"revenue_total", "cost_total", "net_result", "net_margin_pct", "roi_pct", "payback_months", "decision_candidate"}
        if not isinstance(scenario, dict) or set(scenario) != fields:
            raise ValueError(f"scenarios.{name} tiene estructura inválida")
        for field in ("revenue_total", "cost_total"):
            if not _finite_number(scenario[field]) or scenario[field] < 0:
                raise ValueError(f"scenarios.{name}.{field} debe ser finito y no negativo")
        if not _finite_number(scenario["net_result"]):
            raise ValueError(f"scenarios.{name}.net_result debe ser finito")
        for field in ("net_margin_pct", "roi_pct", "payback_months"):
            value = scenario[field]
            if value is not None and not _finite_number(value):
                raise ValueError(f"scenarios.{name}.{field} debe ser finito o null")
        if scenario["payback_months"] is not None and scenario["payback_months"] < 0:
            raise ValueError(f"scenarios.{name}.payback_months no puede ser negativo")
        if scenario["decision_candidate"] not in _DECISIONS:
            raise ValueError(f"scenarios.{name}.decision_candidate inválido")
        if not math.isclose(float(scenario["net_result"]), float(scenario["revenue_total"]) - float(scenario["cost_total"]), rel_tol=0, abs_tol=0.011):
            raise ValueError(f"scenarios.{name}.net_result no coincide con ingresos menos costos")
    if record["decision_candidate"] not in _DECISIONS or record["decision_candidate"] != scenarios["base"]["decision_candidate"]:
        raise ValueError("decision_candidate debe coincidir con el escenario base")
    if not isinstance(record["risk_flags"], list) or any(not isinstance(x, str) for x in record["risk_flags"]):
        raise ValueError("risk_flags debe ser una lista de texto")
    if not isinstance(record["assumptions"], list) or not record["assumptions"] or any(not isinstance(x, str) or not x.strip() for x in record["assumptions"]):
        raise ValueError("assumptions requiere al menos un supuesto no vacío")
    evidence = record["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence requiere al menos una fuente")
    evidence_ids = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ValueError(f"evidence[{index}] debe ser un objeto")
        identifier, source, digest = item.get("evidence_id"), item.get("source"), item.get("digest")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in evidence_ids:
            raise ValueError(f"evidence[{index}].evidence_id inválido o duplicado")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"evidence[{index}].source requerido")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise ValueError(f"evidence[{index}].digest debe ser SHA-256")
        _aware_timestamp(item.get("observed_at"), f"evidence[{index}].observed_at")
        evidence_ids.add(identifier)
    if record["evidence_status"] != "declared_digest_not_source_authentication":
        raise ValueError("evidence_status inválido")
    uncertainty = record["uncertainty"]
    if not isinstance(uncertainty, dict) or uncertainty.get("status") != "not_probability_calibrated" or not isinstance(uncertainty.get("note"), str):
        raise ValueError("uncertainty debe declarar que los escenarios no están calibrados")
    provenance = record["provenance"]
    if not isinstance(provenance, dict) or not isinstance(provenance.get("input_sha256"), str) or not _SHA256_RE.fullmatch(provenance["input_sha256"]):
        raise ValueError("provenance.input_sha256 debe ser SHA-256")
    if record["evaluation_hash"] != _opportunity_hash(record):
        raise ValueError("evaluation_hash no coincide con el contenido económico")
    if record["analysis_only"] is not True or record["orders_created"] is not False or record["orders_executed"] is not False:
        raise ValueError("EconomicOpportunityResult viola los límites de no ejecución")
    if record["authorization"] != "NOT_GRANTED" or record["independent_acceptance_required"] is not True:
        raise ValueError("EconomicOpportunityResult requiere autorización humana y aceptación independiente")


def _validate_result(record: dict[str, Any]) -> None:
    if record.get("evaluation_domain") == "business_opportunity":
        _validate_economic_opportunity_result(record)
    else:
        _validate_decision_result(record)


def append_result(record: dict[str, Any], path: str | Path | None = None) -> str:
    """Validate and append a DecisionResult or EconomicOpportunityResult.

    Writes JSONL with an exclusive POSIX lock, fsync and 0600 permissions.
    The ID is checked for uniqueness while holding the same lock.
    """
    if not isinstance(record, dict):
        raise TypeError("El resultado debe ser un objeto")
    _validate_result(record)
    result_id = record.get("result_id")
    if not isinstance(result_id, str) or not result_id.strip():
        raise ValueError("El resultado debe tener un result_id válido")
    target = Path(path) if path else default_result_store_path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    line = json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n"
    fd = os.open(str(target), os.O_CREAT | os.O_RDWR | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, "r+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                stream.seek(0)
                for existing_line in stream:
                    if not existing_line.strip():
                        continue
                    try:
                        existing = json.loads(existing_line)
                    except json.JSONDecodeError as exc:
                        raise ValueError("ResultStore contiene una línea JSON inválida; append bloqueado") from exc
                    if isinstance(existing, dict) and existing.get("result_id") == result_id:
                        raise ValueError(f"result_id duplicado: {result_id}")
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


def get_result(result_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    """Stream the JSONL file and return one result by ID without loading it all."""
    if not isinstance(result_id, str) or not result_id.strip():
        raise ValueError("result_id requerido")
    target = Path(path) if path else default_result_store_path()
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and record.get("result_id") == result_id:
                return record
    return None
