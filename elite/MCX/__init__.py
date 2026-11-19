"""
MCX — Gobernanza Central de CatedralX
Veredicto multi-criterio, vetos duros y política inmutable.
"""
from .multicriteria import (
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
