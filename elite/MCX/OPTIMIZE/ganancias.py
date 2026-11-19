"""
ganancias.py — Métricas de rendimiento, rentabilidad y riesgo
Chalamandra Magistral DecoX · CatedralX

Cálculos objetivos de resultados del sistema. No predicen — miden lo ocurrido.
"""
from __future__ import annotations

import math
from typing import Sequence


def rendimiento_porcentaje(precio_entrada: float, precio_salida: float) -> float:
    """
    Calcula el rendimiento porcentual de una operación.
    
    Ejemplo: entrada=1000, salida=1050 → 5.0
    """
    if precio_entrada <= 0:
        raise ValueError("El precio de entrada debe ser positivo")
    return ((precio_salida - precio_entrada) / precio_entrada) * 100


def pnl(precio_entrada: float, precio_salida: float, tamano: float = 1.0) -> float:
    """
    Profit & Loss — Ganancia o pérdida absoluta.
    Positivo = ganancia, Negativo = pérdida.
    """
    return (precio_salida - precio_entrada) * tamano


def tasa_acierto(operaciones_exitosas: int, total_operaciones: int) -> float:
    """
    Porcentaje de operaciones con resultado positivo.
    """
    if total_operaciones <= 0:
        return 0.0
    return (operaciones_exitosas / total_operaciones) * 100


def rendimiento_esperado(tasa_acierto_pct: float, ganancia_promedio: float, perdida_promedio: float) -> float:
    """
    Valor esperado por operación:
    (prob_ganar × ganancia_prom) − (prob_perder × perdida_prom)
    
    > 0 → sistema rentable a largo plazo
    """
    p_ganar = tasa_acierto_pct / 100.0
    p_perder = 1.0 - p_ganar
    return (p_ganar * ganancia_promedio) - (p_perder * perdida_promedio)


def factor_profit(ganancias: Sequence[float], perdidas: Sequence[float]) -> float:
    """
    Ratio entre ganancia total y pérdida total.
    
    > 1.5 = aceptable
    > 2.0 = sólido
    > 3.0 = excelente
    """
    suma_ganancias = sum(g for g in ganancias if g > 0)
    suma_perdidas = abs(sum(p for p in perdidas if p < 0))
    
    if suma_perdidas == 0:
        return float("inf") if suma_ganancias > 0 else 0.0
    return suma_ganancias / suma_perdidas


def maximo_drawdown(precios: Sequence[float]) -> float:
    """
    Mayor caída desde un pico hasta un valle, en porcentaje.
    Medida de riesgo: cuánto se perdió en el peor momento.
    """
    if len(precios) < 2:
        return 0.0
    
    maximo = precios[0]
    peor_caida = 0.0
    
    for p in precios:
        if p > maximo:
            maximo = p
        caida = ((maximo - p) / maximo) * 100
        if caida > peor_caida:
            peor_caida = caida
    
    return peor_caida


def sharpe_ratio(rendimientos: Sequence[float], tasa_sin_riesgo: float = 0.0) -> float:
    """
    Rentabilidad extra por unidad de riesgo.
    
    > 0 → mejor que no operar
    > 1.0 → aceptable
    > 1.5 → bueno
    """
    import statistics
    n = len(rendimientos)
    if n < 2:
        return 0.0
    
    media = statistics.mean(rendimientos)
    desv = statistics.pstdev(rendimientos)
    
    if desv == 0:
        return 0.0
    return (media - tasa_sin_riesgo) / desv
