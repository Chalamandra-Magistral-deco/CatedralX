"""Canonical MCX import surface for the multicriteria governance engine.

The implementation remains in REASON temporarily for backward compatibility.
This module exposes the MCX-owned public API without duplicating policy logic.
"""
from ..REASON.multicriteria import (
    CathedralEvaluation,
    blocked_uncertainty,
    compute_evaluation_hash,
    verify_evaluation_hash,
    evaluation_policy,
)

__all__ = [
    "CathedralEvaluation",
    "blocked_uncertainty",
    "compute_evaluation_hash",
    "verify_evaluation_hash",
    "evaluation_policy",
]
