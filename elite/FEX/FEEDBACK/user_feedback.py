"""Human feedback ledger for CatedralX outputs.

Feedback is evidence for review, not authority to modify decision policy.
Records are append-only, contain no user identity field, and live outside the repo.
"""
from __future__ import annotations

import fcntl
import json
import math
import os
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
ASSESSMENTS = ("useful", "partly_useful", "not_useful", "unclear", "incorrect")
REASON_CODES = (
    "unspecified", "correctness", "clarity", "relevance",
    "missing_context", "level_of_detail", "workflow", "other",
)
NEXT_STEPS = ("none", "explain", "verify", "revise", "human_review")
MIN_SAMPLE_SIZE_FOR_TREND = 5
MAX_CORRECTION_LENGTH = 1000
_ALLOWED_FIELDS = {
    "result_id", "cycle_id", "rating", "assessment",
    "reason_code", "preferred_next_step", "correction",
}
_REPO_ROOT = Path(__file__).resolve().parents[3]


def user_feedback_path() -> Path:
    """Return the external append-only path for user feedback."""
    return _target_path(None)


def _target_path(path: str | Path | None) -> Path:
    configured = os.environ.get("CATEDRALX_USER_FEEDBACK_PATH")
    candidate = (
        Path(path).expanduser()
        if path is not None
        else Path(configured).expanduser()
        if configured
        else Path.home() / ".local/state/chalamandra/catedralx/user_feedback.jsonl"
    )
    resolved = candidate.resolve()
    if resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents:
        raise ValueError("El ledger de feedback debe quedar fuera del repositorio.")
    return resolved


def _identifier(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} debe ser una cadena no vacía cuando se proporciona.")
    cleaned = value.strip()
    if len(cleaned) > 128:
        raise ValueError(f"{field} excede 128 caracteres.")
    return cleaned


def record_user_feedback(
    feedback: dict[str, Any],
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate and append one user response; return a clear acknowledgement."""
    if not isinstance(feedback, dict):
        raise TypeError("feedback debe ser un objeto.")
    unknown = sorted(set(feedback) - _ALLOWED_FIELDS)
    if unknown:
        raise ValueError("Campos no permitidos en feedback: " + ", ".join(unknown))

    result_id = _identifier(feedback.get("result_id"), "result_id")
    cycle_id = _identifier(feedback.get("cycle_id"), "cycle_id")
    if result_id is None and cycle_id is None:
        raise ValueError("Se requiere result_id o cycle_id para asegurar trazabilidad.")

    rating = feedback.get("rating")
    if type(rating) is not int or not 1 <= rating <= 5:
        raise ValueError("rating debe ser un entero exacto entre 1 y 5.")

    assessment = feedback.get("assessment")
    if not isinstance(assessment, str) or assessment not in ASSESSMENTS:
        raise ValueError("assessment debe ser uno de: " + ", ".join(ASSESSMENTS))

    reason_code = feedback.get("reason_code", "unspecified")
    if not isinstance(reason_code, str) or reason_code not in REASON_CODES:
        raise ValueError("reason_code debe ser uno de: " + ", ".join(REASON_CODES))

    next_step = feedback.get("preferred_next_step", "none")
    if not isinstance(next_step, str) or next_step not in NEXT_STEPS:
        raise ValueError("preferred_next_step debe ser uno de: " + ", ".join(NEXT_STEPS))

    correction = feedback.get("correction")
    if correction is not None:
        if not isinstance(correction, str):
            raise ValueError("correction debe ser texto.")
        correction = correction.strip()
        if len(correction) > MAX_CORRECTION_LENGTH:
            raise ValueError(f"correction no debe exceder {MAX_CORRECTION_LENGTH} caracteres.")

    target = _target_path(path)
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "user_feedback",
        "feedback_id": str(uuid.uuid4()),
        "recorded_at": datetime.now(UTC).isoformat(),
        "result_id": result_id,
        "cycle_id": cycle_id,
        "rating": rating,
        "assessment": assessment,
        "reason_code": reason_code,
        "preferred_next_step": next_step,
        "correction": correction,
        "controls": {
            "append_only": True,
            "changes_policy": False,
            "automatic_retraining": False,
            "trading_enabled": False,
            "orders_created": False,
            "orders_executed": False,
        },
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(
        record, ensure_ascii=False, sort_keys=True, allow_nan=False
    ) + "\n").encode("utf-8")
    descriptor = os.open(target, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("No se pudo completar la escritura del feedback.")
            remaining = remaining[written:]
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    return {
        "status": "FEEDBACK_RECORDED_FOR_REVIEW",
        "feedback_id": record["feedback_id"],
        "result_id": result_id,
        "cycle_id": cycle_id,
        "message": (
            "Feedback registrado para análisis. No cambia automáticamente "
            "las reglas, los umbrales ni los permisos del sistema."
        ),
        "policy_changed": False,
        "automatic_retraining": False,
        "orders_executed": False,
    }


def summarize_user_feedback(
    path: str | Path | None = None,
    *,
    min_sample_size: int = MIN_SAMPLE_SIZE_FOR_TREND,
) -> dict[str, Any]:
    """Aggregate feedback into review signals; never applies changes automatically."""
    if type(min_sample_size) is not int or min_sample_size < 1:
        raise ValueError("min_sample_size debe ser entero positivo.")
    target = _target_path(path)
    records: list[dict[str, Any]] = []
    if target.exists():
        with target.open("r", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
            try:
                for line_number, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"Ledger de feedback inválido en línea {line_number}.") from exc
                    required_fields = {
                        "schema_version", "record_type", "feedback_id", "recorded_at",
                        "result_id", "cycle_id", "rating", "assessment", "reason_code",
                        "preferred_next_step", "correction", "controls",
                    }
                    if (
                        not isinstance(record, dict)
                        or set(record) != required_fields
                        or record.get("record_type") != "user_feedback"
                        or record.get("schema_version") != SCHEMA_VERSION
                    ):
                        raise ValueError(f"Registro de feedback inválido en línea {line_number}.")
                    rating = record.get("rating")
                    if type(rating) is not int or not 1 <= rating <= 5:
                        raise ValueError(f"Rating inválido en línea {line_number}.")
                    if (
                        record.get("assessment") not in ASSESSMENTS
                        or record.get("reason_code") not in REASON_CODES
                        or record.get("preferred_next_step") not in NEXT_STEPS
                    ):
                        raise ValueError(f"Categorías inválidas en línea {line_number}.")
                    if not record.get("result_id") and not record.get("cycle_id"):
                        raise ValueError(f"Registro sin trazabilidad en línea {line_number}.")
                    if not isinstance(record.get("feedback_id"), str) or not record["feedback_id"].strip():
                        raise ValueError(f"feedback_id inválido en línea {line_number}.")
                    correction = record.get("correction")
                    if correction is not None and (
                        not isinstance(correction, str) or len(correction) > MAX_CORRECTION_LENGTH
                    ):
                        raise ValueError(f"correction inválida en línea {line_number}.")
                    records.append(record)
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    count = len(records)
    ratings = [record["rating"] for record in records]
    average = round(sum(ratings) / count, 2) if count else None
    assessments = Counter(record["assessment"] for record in records)
    reasons = Counter(record["reason_code"] for record in records)
    next_steps = Counter(record["preferred_next_step"] for record in records)
    recommendations: list[str] = []

    if count < min_sample_size:
        recommendations.append("COLLECT_MORE_FEEDBACK_BEFORE_GENERALIZING")
    else:
        low_ratings = sum(rating <= 2 for rating in ratings)
        issue_floor = max(2, math.ceil(count * 0.2))
        if (average is not None and average < 3.5) or low_ratings >= issue_floor:
            recommendations.append("MANUAL_REVIEW_OF_ANSWER_QUALITY")
        if assessments["incorrect"] > 0 or reasons["correctness"] >= issue_floor:
            recommendations.append("VERIFY_CORRECTNESS_AND_EVIDENCE_PATH")
        if assessments["unclear"] >= issue_floor or reasons["clarity"] >= issue_floor:
            recommendations.append("REVIEW_RESPONSE_CLARITY_AND_EXPLANATION")
        if reasons["missing_context"] >= issue_floor:
            recommendations.append("REVIEW_REQUIRED_CONTEXT_FIELDS")
        if not recommendations:
            recommendations.append("NO_SYSTEM_CHANGE_INDICATED_BY_CURRENT_SAMPLE")

    return {
        "schema_version": SCHEMA_VERSION,
        "report_status": "ok",
        "feedback_count": count,
        "average_rating": average,
        "assessment_counts": {key: assessments.get(key, 0) for key in ASSESSMENTS},
        "reason_counts": {key: reasons.get(key, 0) for key in REASON_CODES},
        "preferred_next_step_counts": {key: next_steps.get(key, 0) for key in NEXT_STEPS},
        "minimum_sample_size_for_trend": min_sample_size,
        "review_required": count >= min_sample_size and any(
            action != "NO_SYSTEM_CHANGE_INDICATED_BY_CURRENT_SAMPLE"
            for action in recommendations
        ),
        "recommended_actions": recommendations,
        "automatic_policy_changes": False,
        "automatic_retraining": False,
        "trading_enabled": False,
        "orders_created": False,
        "orders_executed": False,
        "disclaimer": (
            "El feedback es una señal de experiencia del usuario, no prueba factual. "
            "Las correcciones requieren contraste con evidencia y aprobación humana."
        ),
    }

