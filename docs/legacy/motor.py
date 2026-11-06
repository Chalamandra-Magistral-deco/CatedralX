#!/usr/bin/env python3
"""DEPRECATED: Use BIN/catedral motor - wrapper mantenido por compatibilidad."""
import sys
from pathlib import Path

print("DEPRECATED: BIN/motor.py -> use BIN/catedral motor", file=sys.stderr)
ROOT = Path(__file__).resolve().parents[1]
ELITE = ROOT / "elite"
if str(ELITE) not in sys.path:
    sys.path.insert(0, str(ELITE))
from REASON.razon import main

if __name__ == "__main__":
    raise SystemExit(main())
