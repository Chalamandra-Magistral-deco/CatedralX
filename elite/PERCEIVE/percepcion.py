"""Translate validated RSX payloads into the SCX sensory contract."""
from __future__ import annotations

from typing import Any

from REASON.schemas import SensoryInput

from .sensors import normalize_market_payload


def construir_sensory_input(payload: dict[str, Any], free_energy_prev: float = 0.0) -> SensoryInput:
    data = normalize_market_payload(payload)
    return SensoryInput(precio_historico=data["historial_precios"], precio_actual=data["precio"],
                        gap=data["gap"], inercia=data["inercia"], free_energy_prev=free_energy_prev)

def from_snapshot(snapshot: dict[str, Any], free_energy_prev: float = 0.0) -> SensoryInput:
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("PERCEIVE"), dict):
        raise ValueError("snapshot must contain a PERCEIVE object")

    dynamic_constraints = snapshot.get("DYNAMIC_CONSTRAINTS", {})
    if not isinstance(dynamic_constraints, dict):
        raise ValueError("DYNAMIC_CONSTRAINTS debe ser un objeto cuando se proporciona")

    central_dimensions_bp = snapshot.get("CENTRAL_DIMENSIONS_BP", {})
    if not isinstance(central_dimensions_bp, dict):
        raise ValueError("CENTRAL_DIMENSIONS_BP debe ser un objeto cuando se proporciona")

    sensory = construir_sensory_input(snapshot["PERCEIVE"], free_energy_prev)
    sensory.dynamic_constraints = dict(dynamic_constraints)
    sensory.central_dimensions_bp = dict(central_dimensions_bp)
    return sensory
