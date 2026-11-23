"""Cognitive capacity monitor — how much processing headroom remains.
Pure function — reads metrics, returns a reading. Never decides or acts.
Mapa MCX/OPTIMIZE: Estima carga cognitiva y margen disponible.
Analogía: Indicador de combustible. Dice cuánto queda, no decide cuándo parar.
"""
from enum import Enum
from typing import NamedTuple


class EstadoCognitivo(str, Enum):
    DESCANSANDO = "descansando"
    OPERANDO = "operando"
    SATURADO = "saturado"
    CRITICO = "crítico"  # ✅ Con tilde — compatibilidad con consumidores


class EstadoCognitivoResultado(NamedTuple):
    uso: float
    estado: EstadoCognitivo
    capacidad_libre: float


def estado_cognitivo(
    tareas_activas: float,
    capacidad_maxima: float,
) -> EstadoCognitivoResultado:
    """
    Estimate current cognitive load and remaining capacity.

    Arguments:
        tareas_activas:       Carga de trabajo actual
        capacidad_maxima:     Límite operativo del contexto

    Returns:
        uso:                 [0.0, 1.0] — fracción de capacidad ocupada
        estado:              etiqueta para interpretación
        capacidad_libre:     margen disponible antes de saturación
    """
    if capacidad_maxima <= 0:
        return EstadoCognitivoResultado(1.0, EstadoCognitivo.CRITICO, 0.0)

    if tareas_activas < 0:
        raise ValueError("tareas_activas no puede ser negativo")
    if capacidad_maxima < 0:
        raise ValueError("capacidad_maxima no puede ser negativa")

    porcentaje_usado = max(0.0, min(1.0, tareas_activas / capacidad_maxima))
    capacidad_libre = 1.0 - porcentaje_usado

    if porcentaje_usado < 0.5:
        estado = EstadoCognitivo.DESCANSANDO
    elif porcentaje_usado < 0.8:
        estado = EstadoCognitivo.OPERANDO
    elif porcentaje_usado < 0.95:
        estado = EstadoCognitivo.SATURADO
    else:
        estado = EstadoCognitivo.CRITICO

    return EstadoCognitivoResultado(porcentaje_usado, estado, capacidad_libre)
