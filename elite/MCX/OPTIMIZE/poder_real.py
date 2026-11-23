"""System power and conversion efficiency — useful output vs resources consumed.
Pure function — observes, does not adjust or optimize. Read-only metric.
Mapa MCX/OPTIMIZE: Mide rendimiento y desperdicio de recursos.
Analogía: Vatímetro. Mide entrada vs trabajo útil. No cambia la instalación.
"""


def rendimiento_potencia(
    potencia_entrada: float,
    potencia_util: float,
) -> float:
    """
    Calculate conversion efficiency: useful output / total resources used.

    Arguments:
        potencia_entrada:     Recursos totales consumidos
        potencia_util:        Trabajo que realmente avanza el sistema

    Returns:
        rendimiento:          [0.0, 1.0] — 1.0 = sin desperdicio
    """
    if potencia_entrada <= 0:
        return 0.0
    if potencia_util < 0:
        raise ValueError("potencia_util no puede ser negativo")
    if potencia_util > potencia_entrada:
        raise ValueError(
            f"potencia_util no puede exceder potencia_entrada: "
            f"{potencia_util} > {potencia_entrada}"
        )

    return max(0.0, min(1.0, potencia_util / potencia_entrada))
