"""Opt-in FEX feedback adapter with explicit storage and no automatic learning.

This adapter delegates to the existing append-only feedback ledger. It refuses
implicit/default storage paths so callers cannot accidentally write user state.
It computes reports only; it never trains models or executes orders.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from FEX.FEEDBACK.feedback_loop import (
    evaluar_feedback,
    registrar_prediccion,
    registrar_resultado,
    resumir_memoria_decisiones,
)


def record_prediction(*, path: str | Path, prediction: dict[str, Any],
                      prediction_id: str | None = None) -> str:
    """Record a prediction only at an explicitly supplied ledger path."""
    target = _explicit_path(path)
    return registrar_prediccion(prediction, path=target, prediction_id=prediction_id)


def record_observed_outcome(*, path: str | Path, prediction_id: str,
                            outcome: dict[str, Any]) -> str:
    """Append a label from an actually observed outcome to an explicit ledger."""
    target = _explicit_path(path)
    written_to = registrar_resultado(prediction_id, outcome, path=target)
    return str(written_to)


def evaluate_ledger(*, path: str | Path) -> dict[str, Any]:
    """Evaluate labeled records offline; never trains or changes operating mode."""
    target = _explicit_path(path)
    report = evaluar_feedback(path=target)
    report["adapter_status"] = "explicit_path_only"
    report["automatic_retraining"] = False
    report["trading_enabled"] = False
    report["orders_executed"] = False
    return report


def summarize_observed_decisions(decisions: list[str],
                                 max_history: int = 50) -> dict[str, Any]:
    """Summarize caller-supplied observed labels without inventing outcomes."""
    return resumir_memoria_decisiones(decisions, max_history=max_history)


def _explicit_path(path: str | Path | None) -> Path:
    if path is None or not str(path).strip():
        raise ValueError("Se requiere una ruta explícita para el ledger FEX; no se usa la ruta predeterminada.")
    return Path(path).expanduser()
