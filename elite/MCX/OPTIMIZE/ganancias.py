"""Performance metrics — return, drawdown, and efficiency ratios.
Pure functions: compute statistics, do not store or modify history.
Mapa MCX/OPTIMIZE: Métricas de rendimiento sin persistencia.
"""
from typing import Sequence


def rendimiento(
    valor_inicial: float,
    valor_final: float,
) -> float:
    """Return = (final / initial) - 1"""
    if valor_inicial <= 0:
        return 0.0
    return (valor_final / valor_inicial) - 1.0


def maximo_descenso(
    valores: Sequence[float],
) -> float:
    """Maximum peak-to-trough loss, returns fraction ≥ 0.0"""
    if not valores or len(valores) < 2:
        return 0.0

    pico = valores[0]
    if pico <= 0:
        return 0.0

    descenso_max = 0.0

    for v in valores[1:]:
        if v > pico:
            pico = v
        else:
            descenso = (pico - v) / pico
            descenso_max = max(descenso_max, descenso)

    return descenso_max
