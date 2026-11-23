"""Kelly-Vince criterion — optimal position sizing based on edge and risk.
Pure function: calculates fraction, does NOT execute trades.
Mapa MCX/OPTIMIZE: Tamaño de posición óptimo con límite conservador.
"""


def fraccion_kelly(
    tasa_exito: float,
    ganancia: float,
    perdida: float,
    fraccion_conservadora: float = 0.5,
) -> float:
    """
    Calculate Kelly Criterion and apply conservative fraction.

    Arguments:
        tasa_exito:             probabilidad de ganar [0.0, 1.0]
        ganancia:              múltiplo si gana (> 0)
        perdida:               pérdida por unidad si pierde (> 0, sin límite superior)
        fraccion_conservadora: factor de reducción, típicamente 0.5

    Returns:
        fraccion_capital: qué porcentaje usar [0.0, 1.0]
    """
    if not (0.0 <= tasa_exito <= 1.0):
        raise ValueError(f"tasa_exito fuera de rango [0,1]: {tasa_exito}")
    if ganancia <= 0:
        raise ValueError(f"ganancia debe ser > 0: {ganancia}")
    if perdida <= 0:
        raise ValueError(f"perdida debe ser > 0: {perdida}")
    if not (0.0 < fraccion_conservadora <= 1.0):
        raise ValueError(
            f"fraccion_conservadora fuera de rango (0,1]: {fraccion_conservadora}"
        )

    p = tasa_exito
    q = 1.0 - p
    b = ganancia / perdida
    kelly_crudo = p - (q / b)
    fraccion = max(0.0, kelly_crudo * fraccion_conservadora)
    return min(1.0, fraccion)
