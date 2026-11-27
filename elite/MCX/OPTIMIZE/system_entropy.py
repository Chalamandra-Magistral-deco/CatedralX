"""
System entropy — Bounds on sustained order in open systems
Chalamandra Magistral DecoX · CatedralX

Formaliza la segunda ley para el sistema: el orden interno
solo se mantiene si se exporta desorden al entorno.
No es decoración: es la restricción de sostenibilidad del bucle.
"""
from __future__ import annotations

import math
from typing import Tuple


def tasa_entropia(
    produccion_interna: float,
    intercambio_entorno: float = 0.0,
) -> Tuple[float, float]:
    if produccion_interna < 0:
        raise ValueError("Producción interna de entropía no puede ser negativa")
    
    dS_total = intercambio_entorno + produccion_interna
    return dS_total, produccion_interna


def orden_sostenido(
    energia_entrante: float,
    desorden_exportado: float,
    produccion_interna: float,
    umbral_minimo: float = 0.0,
) -> dict[str, float | bool]:
    dS_total = desorden_exportado + produccion_interna
    sostenible = dS_total <= umbral_minimo
    margen = umbral_minimo - dS_total
    eficiencia = min(1.0, max(0.0, abs(desorden_exportado) / max(energia_entrante, 1e-12)))
    
    return {
        "tasa_total": round(dS_total, 8),
        "produccion_interna": round(produccion_interna, 8),
        "desorden_exportado": round(desorden_exportado, 8),
        "margen": round(margen, 8),
        "sostenible": sostenible,
        "eficiencia_exportacion": round(eficiencia, 6),
    }


def limite_degradacion(
    ciclos: int,
    tasa_degradacion: float = 0.015,
) -> float:
    if ciclos < 0:
        raise ValueError("Los ciclos no pueden ser negativos")
    return math.exp(-tasa_degradacion * ciclos)
