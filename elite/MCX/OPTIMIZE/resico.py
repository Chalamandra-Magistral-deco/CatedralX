"""
resico.py — Resistencia y consolidación del sistema
Chalamandra Magistral DecoX · CatedralX

Mide la capacidad del sistema para absorber perturbaciones
y mantener su estado estable sin degradarse.
"""
from __future__ import annotations


def resistencia(
    fatiga: float,
    riesgo: float,
    ciclos_estables: int,
) -> dict[str, float | bool]:
    """
    Capacidad de resistir sin colapsar.
    
    Se fortalece con más ciclos estables; se debilita con fatiga y riesgo.
    """
    if not (0 <= fatiga <= 1 and 0 <= riesgo <= 1):
        raise ValueError("fatiga y riesgo deben estar entre 0 y 1")
    if ciclos_estables < 0:
        raise ValueError("ciclos_estables no puede ser negativo")

    base = 1.0 - (fatiga + riesgo) / 2.0
    experiencia = min(0.3, ciclos_estables / 500.0)
    indice_resistencia = max(0.0, min(1.0, base + experiencia))

    return {
        "resistencia": round(indice_resistencia, 6),
        "estable": indice_resistencia >= 0.5,
        "nivel": (
            "sólido" if indice_resistencia >= 0.75 else
            "moderado" if indice_resistencia >= 0.5 else
            "débil"
        ),
    }


def consolidacion(
    resistencia_actual: float,
    ciclos_ganados: int,
    factor_aprendizaje: float = 0.02,
) -> dict[str, float]:
    """
    Convierte estabilidad repetida en mayor solidez estructural.
    Cada ciclo exitoso refuerza levemente el sistema.
    """
    if not (0 <= resistencia_actual <= 1):
        raise ValueError("resistencia_actual debe estar entre 0 y 1")
    if ciclos_ganados < 0:
        raise ValueError("ciclos_ganados no puede ser negativo")

    incremento = min(0.5, ciclos_ganados * factor_aprendizaje)
    nuevo_nivel = min(1.0, resistencia_actual + incremento)

    return {
        "anterior": round(resistencia_actual, 6),
        "incremento": round(nuevo_nivel - resistencia_actual, 6),
        "nuevo": round(nuevo_nivel, 6),
    }


def estimar_reserva(ingreso: float, tasa: float = 0.02) -> dict:
    ingreso, tasa = float(ingreso), float(tasa)
    if ingreso < 0 or not 0 <= tasa <= 1:
        raise ValueError("ingreso must be >= 0 and tasa must be between 0 and 1")
    return {"ingreso": round(ingreso, 2), "tasa_configurada": tasa,
            "reserva_estimada": round(ingreso * tasa, 2),
            "disclaimer": "Estimación configurable; no determina la obligación fiscal real."}
