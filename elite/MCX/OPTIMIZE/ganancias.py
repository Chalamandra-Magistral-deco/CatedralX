"""Append-only results ledger; this module never places orders."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Sequence


def ledger_path() -> Path:
    return Path(os.environ.get("CATEDRALX_LEDGER_PATH", str(Path.home()/".local/state/chalamandra/catedralx/ledger.jsonl"))).expanduser()

def registrar_resultado(record: dict, path: str | Path | None = None) -> Path:
    target = Path(path).expanduser() if path else ledger_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    safe = dict(record)
    safe["orders_executed_by_this_module"] = False
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe, ensure_ascii=False, allow_nan=False) + "\n")
    return target


# Backward-compatible financial metrics retained alongside the append-only ledger.
def rendimiento_porcentaje(precio_entrada: float, precio_salida: float) -> float:
    """Return percentage return between entry and exit prices."""
    if precio_entrada <= 0:
        raise ValueError("El precio de entrada debe ser positivo")
    return ((precio_salida - precio_entrada) / precio_entrada) * 100


def pnl(precio_entrada: float, precio_salida: float, tamano: float = 1.0) -> float:
    """Return absolute profit/loss for the supplied position size."""
    return (precio_salida - precio_entrada) * tamano


def tasa_acierto(operaciones_exitosas: int, total_operaciones: int) -> float:
    """Return the percentage of profitable operations."""
    if total_operaciones <= 0:
        return 0.0
    return (operaciones_exitosas / total_operaciones) * 100


def rendimiento_esperado(
    tasa_acierto_pct: float, ganancia_promedio: float, perdida_promedio: float
) -> float:
    """Return expected value per operation using win rate and average outcomes."""
    p_ganar = tasa_acierto_pct / 100.0
    p_perder = 1.0 - p_ganar
    return (p_ganar * ganancia_promedio) - (p_perder * perdida_promedio)


def factor_profit(ganancias: Sequence[float], perdidas: Sequence[float]) -> float:
    """Return gross profits divided by gross losses."""
    suma_ganancias = sum(g for g in ganancias if g > 0)
    suma_perdidas = abs(sum(p for p in perdidas if p < 0))
    if suma_perdidas == 0:
        return float("inf") if suma_ganancias > 0 else 0.0
    return suma_ganancias / suma_perdidas


def maximo_drawdown(precios: Sequence[float]) -> float:
    """Return the maximum peak-to-trough drawdown in percentage points."""
    if len(precios) < 2:
        return 0.0
    maximo = precios[0]
    peor_caida = 0.0
    for precio in precios:
        if precio > maximo:
            maximo = precio
        caida = ((maximo - precio) / maximo) * 100
        if caida > peor_caida:
            peor_caida = caida
    return peor_caida


def sharpe_ratio(
    rendimientos: Sequence[float], tasa_sin_riesgo: float = 0.0
) -> float:
    """Return excess mean return divided by population standard deviation."""
    import statistics

    if len(rendimientos) < 2:
        return 0.0
    media = statistics.mean(rendimientos)
    desviacion = statistics.pstdev(rendimientos)
    if desviacion == 0:
        return 0.0
    return (media - tasa_sin_riesgo) / desviacion
