"""Quantum shield: compound risk monitoring and global panic blocking."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List

import psutil

# One configurable source of truth shared by defense and order-generation code.
PATH_PANIC = Path(
    os.path.expanduser(
        os.environ.get("CATEDRALX_PANIC_PATH", "~/LAB/03-OUTPUT/.panic")
    )
)


def riesgo_compuesto(riesgo_ram: float, riesgo_codigo: float) -> float:
    """Combine RAM and code risk with the system's configured weights."""
    return 0.55 * riesgo_ram + 0.45 * riesgo_codigo


def riesgo_ram_monitor() -> float:
    """Return RAM pressure normalized to one at 90 percent usage."""
    uso = psutil.virtual_memory().percent
    return max(0.0, min(1.0, uso / 90.0))


def limitar_tasa(
    timestamps: List[float],
    max_calls: int = 10,
    ventana: int = 60,
) -> bool:
    """Record a call and report whether the rolling limit is reached."""
    ahora = time.time()
    while timestamps and ahora - timestamps[0] > ventana:
        timestamps.pop(0)
    if len(timestamps) >= max_calls:
        return True
    timestamps.append(ahora)
    return False


def _panic_path() -> Path:
    """Resolve the current shared panic path, including test/runtime overrides."""
    return Path(PATH_PANIC).expanduser()


def activar_panic(reason: str = "RIESGO_ALTO") -> None:
    """Create the global panic marker with the supplied reason."""
    path = _panic_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(reason), encoding="utf-8")


def desactivar_panic() -> None:
    """Remove the global panic marker when it exists."""
    path = _panic_path()
    if path.exists():
        path.unlink()


def estado_defensivo(estado_sistema: Dict[str, Any]) -> Dict[str, Any]:
    """Return normalized risk details and current blocking state."""
    riesgo_ram = riesgo_ram_monitor()
    riesgo_codigo = estado_sistema.get("entropia", 0.5)
    total = riesgo_compuesto(riesgo_ram, riesgo_codigo)
    return {
        "riesgo_total": round(total, 4),
        "riesgo_ram": round(riesgo_ram, 4),
        "riesgo_codigo": round(riesgo_codigo, 4),
        "bloqueo_activo": total > 0.85,
        "panic_activo": _panic_path().exists(),
    }
