#!/usr/bin/env python3
"""Append user feedback or print an aggregate, read-only feedback report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ELITE_DIR = Path(__file__).resolve().parents[1]
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))

from FEX.FEEDBACK.user_feedback import (
    ASSESSMENTS,
    NEXT_STEPS,
    REASON_CODES,
    record_user_feedback,
    summarize_user_feedback,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="Mostrar agregado de solo lectura")
    parser.add_argument("--path", help="Ruta externa opcional del ledger JSONL")
    parser.add_argument("--result-id", help="ID del resultado evaluado")
    parser.add_argument("--cycle-id", help="ID del ciclo evaluado")
    parser.add_argument("--rating", type=int, choices=range(1, 6), help="Calificación de 1 a 5")
    parser.add_argument("--assessment", choices=ASSESSMENTS)
    parser.add_argument("--reason-code", choices=REASON_CODES, default="unspecified")
    parser.add_argument("--preferred-next-step", choices=NEXT_STEPS, default="none")
    parser.add_argument(
        "--correction",
        help="Corrección opcional (máximo 1000 caracteres; no incluyas secretos ni datos personales)",
    )
    args = parser.parse_args()

    try:
        if args.report:
            if any(value is not None for value in (
                args.result_id, args.cycle_id, args.rating, args.assessment, args.correction
            )):
                raise ValueError("--report no se combina con campos para registrar feedback.")
            result = summarize_user_feedback(args.path)
        else:
            if args.rating is None or args.assessment is None:
                raise ValueError("Para registrar feedback se requieren --rating y --assessment.")
            result = record_user_feedback(
                {
                    "result_id": args.result_id,
                    "cycle_id": args.cycle_id,
                    "rating": args.rating,
                    "assessment": args.assessment,
                    "reason_code": args.reason_code,
                    "preferred_next_step": args.preferred_next_step,
                    "correction": args.correction,
                },
                path=args.path,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, TypeError, ValueError) as exc:
        print(json.dumps({
            "status": "FEEDBACK_ERROR",
            "reason": str(exc),
            "policy_changed": False,
            "automatic_retraining": False,
            "orders_executed": False,
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
