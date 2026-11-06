"""Data contracts exchanged by the reasoning orchestrator."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReasonState:
    """Unified market, risk and decision state for the reasoning layer."""

    precio: float = 0.0
    historico: list[float] = field(default_factory=list)
    volatilidad_local: float = 0.0
    gap: float = 0.0
    microtrend: float = 0.0
    funding_rate: float = 0.0
    open_interest: float = 0.0
    kelly: float = 0.0
    iv: float = 0.0
    gamma: float = 0.0
    free_energy: float = 0.0
    hamiltoniano: float = 0.0
    sentimiento_riesgo: float = 0.0
    decision: str = "HOLD"
    decision_mode: str = "NEUTRAL"
    confianza: float = 0.0
    size_final: float = 0.0
    timestamp: float = 0.0


@dataclass
class SensoryInput:
    precio_historico: list[float]
    precio_actual: float
    gap: float = 0.0
    inercia: float = 0.0
    free_energy_prev: float = 0.0
    dynamic_constraints: dict[str, Any] = field(default_factory=dict)
    # Explicit upstream governance scores; empty means uncalibrated and blocks acceptance.
    central_dimensions_bp: dict[str, Any] = field(default_factory=dict)


@dataclass
class CathedralState:
    timestamp: int
    decision: str
    confianza: float
    free_energy: float
    neurovector: Any = field(default_factory=dict)
    giroscopio: dict[str, Any] = field(default_factory=dict)
    razon_anarmonica: dict[str, Any] = field(default_factory=dict)
    percepcion_espacial: dict[str, Any] = field(default_factory=dict)
    hamiltoniano: float = 0.0
    energia_cognitiva: float = 0.0
    decisiones: list[dict[str, Any]] = field(default_factory=list)
    regimen: str = "INDEFINIDO"
    señal_combinada: str = "lateral"
    # Optional v4.2 extension; default preserves old positional/keyword constructors.
    cognicion: dict[str, Any] = field(default_factory=dict)
