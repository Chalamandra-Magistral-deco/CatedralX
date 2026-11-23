"""Translate validated RSX payloads into the SCX sensory contract."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from REASON.schemas import SensoryInput

from .sensors import normalize_market_payload


def construir_sensory_input(payload: dict[str, Any], free_energy_prev: float = 0.0) -> SensoryInput:
    data = normalize_market_payload(payload)
    return SensoryInput(
        precio_historico=data["historial_precios"],
        precio_actual=data["precio"],
        gap=data["gap"],
        inercia=data["inercia"],
        free_energy_prev=free_energy_prev,
    )


def validar_campos_gobernanza(snapshot: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate optional governance fields without exposing caller-owned mappings."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a dictionary")
    dynamic_constraints = snapshot.get("DYNAMIC_CONSTRAINTS", {})
    central_dimensions_bp = snapshot.get("CENTRAL_DIMENSIONS_BP", {})
    if not isinstance(dynamic_constraints, dict):
        raise ValueError("DYNAMIC_CONSTRAINTS must be a dictionary when provided")
    if not isinstance(central_dimensions_bp, dict):
        raise ValueError("CENTRAL_DIMENSIONS_BP must be a dictionary when provided")
    if any(not isinstance(key, str) for key in dynamic_constraints):
        raise ValueError("DYNAMIC_CONSTRAINTS keys must be strings")
    allowed_dimensions = {
        "viability_bp", "human_value_bp", "distribution_bp",
        "resilience_bp", "evidence_bp",
    }
    if any(not isinstance(key, str) for key in central_dimensions_bp):
        raise ValueError("CENTRAL_DIMENSIONS_BP keys must be strings")
    unknown = sorted(set(central_dimensions_bp) - allowed_dimensions)
    if unknown:
        raise ValueError("CENTRAL_DIMENSIONS_BP contains unrecognized keys: " + ", ".join(unknown))
    return deepcopy(dynamic_constraints), deepcopy(central_dimensions_bp)


def from_snapshot(snapshot: dict[str, Any], free_energy_prev: float = 0.0) -> SensoryInput:
    if not isinstance(snapshot, dict):
        raise ValueError(f"snapshot must be a dictionary; got {type(snapshot).__name__}")
    perceive = snapshot.get("PERCEIVE")
    if not isinstance(perceive, dict):
        raise ValueError("snapshot must contain a 'PERCEIVE' dictionary section")
    dynamic_constraints, central_dimensions_bp = validar_campos_gobernanza(snapshot)
    sensory = construir_sensory_input(perceive, free_energy_prev)
    sensory.dynamic_constraints = dynamic_constraints
    sensory.central_dimensions_bp = central_dimensions_bp
    return sensory
