"""
Operational fatigue proxy based on cycle count and risk pressure.
Chalamandra Magistral DecoX · CatedralX

Estima el desgaste operativo del sistema a lo largo del tiempo.
"""
from __future__ import annotations


def estado_mental(ciclos: int, cortisol: float) -> dict:
    """
    Calcula fatiga y energía restante del sistema.
    
    Fatiga aumenta con:
      - Número de ciclos operados
      - Nivel de cortisol / presión de riesgo
    
    Devuelve: fatiga [0,1], energía restante [0,1] y marca de métrica aproximada.
    """
    if ciclos < 0:
        raise ValueError("ciclos must be non-negative")
    
    cortisol = min(1.0, max(0.0, float(cortisol)))
    fatigue = min(1.0, ciclos / 1000.0 * 0.5 + cortisol * 0.5)
    
    return {
        "fatiga": round(fatigue, 6),
        "energia": round(1.0 - fatigue, 6),
        "is_proxy_metric": True,
    }