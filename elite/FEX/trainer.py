"""DEPRECATED: Compatibility facade - use FEX.FEEDBACK.trainer

Original: Compatibility facade for the canonical FEX feedback trainer.

The implementation lives in ``FEX.FEEDBACK.trainer``. Keep these legacy names
for callers using the historical ``FEX.trainer`` import path.
"""
from __future__ import annotations

import numpy as np

from FEX.FEEDBACK.trainer import (
    actualizar_modelo as _actualizar_modelo,
)
from FEX.FEEDBACK.trainer import (
    sgd_step as _sgd_step,
)


def sgd_paso(
    pesos: np.ndarray,
    gradiente: np.ndarray,
    tasa: float = 0.01,
) -> np.ndarray:
    return _sgd_step(pesos, gradiente, tasa)


def entrenar_paso(
    entradas: list[float],
    objetivo: float,
    pesos: np.ndarray,
    tasa: float = 0.01,
) -> tuple[np.ndarray, float]:
    return _actualizar_modelo(entradas, objetivo, pesos, tasa)
