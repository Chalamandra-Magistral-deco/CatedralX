#!/usr/bin/env python3
"""Verify a CatedralX evaluation_hash by recomputation (C-2).

Agents only validates ``evaluation_hash`` by format (64 hex chars); this
CLI recomputes it from the evaluation object itself, so a tampered verdict
or scenario cannot pass with a well-formed but wrong hash.

Usage:
    BIN/catedral verify-evaluation-hash --input-file <evaluation.json>
    BIN/catedral verify-evaluation-hash --input-file <evaluation.json> --kind central
    BIN/catedral verify-evaluation-hash --input-file <evaluation.json> --expected <hex>

Input: the evaluation result object itself as JSON:
- kind ``central``: the object returned by
  ``REASON.multicriteria.CathedralEvaluation.evaluate()`` (or
  ``blocked_uncertainty``) — ``status``/``score``/``dimensions`` plus the
  embedded ``evaluation_hash``. The hash covers
  ``{schema_version: 2, policy, result}``; it verifies the verdict and the
  policy, NOT the input prices.
- kind ``opportunity``: the object returned by
  ``REASON.core_contract.evaluate_economic_opportunity`` — the whole result
  (scenarios, financials, evidence) minus its own ``evaluation_hash``.

``--kind auto`` (default) detects the kind: ``evaluation_domain ==
"business_opportunity"`` means opportunity; an object with ``dimensions``
and ``score`` means central. A ``DecisionResult`` (from
``contracts.builder``) CANNOT be verified on its own: it carries the hash
but not the multicriteria result the hash covers — pass the raw evaluation
object instead.

``--expected <hex>`` compares the recomputed hash against that value
instead of the hash embedded in the file (for callers that stripped it).

Output: one JSON object on stdout, e.g.
    {"valid": true, "kind": "central", "expected": "<hex>",
     "computed": "<hex>", "reason": "ok"}

Exit codes: 0 = hash valid; 1 = hash invalid (mismatch, missing or
malformed); 2 = input/usage error (missing file, invalid JSON, unknown
evaluation kind). No orders, no state writes, no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ELITE_DIR = Path(__file__).resolve().parents[1]
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))

from REASON.core_contract import verify_opportunity_evaluation_hash
from REASON.multicriteria import verify_evaluation_hash


def _detect_kind(result: Any) -> str | None:
    if not isinstance(result, dict):
        return None
    if result.get("evaluation_domain") == "business_opportunity":
        return "opportunity"
    if isinstance(result.get("dimensions"), dict) and "score" in result:
        return "central"
    return None


def verify_file(path: str, *, kind: str, expected: str | None) -> tuple[dict[str, Any], int]:
    try:
        result = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"valid": False, "kind": kind, "expected": expected,
                "computed": None, "reason": "input_file_not_found"}, 2
    except (OSError, ValueError, TypeError) as exc:
        return {"valid": False, "kind": kind, "expected": expected,
                "computed": None, "reason": f"input_unreadable: {type(exc).__name__}"}, 2
    detected = _detect_kind(result) if kind == "auto" else kind
    if detected is None:
        return {"valid": False, "kind": kind, "expected": expected,
                "computed": None, "reason": "unknown_evaluation_kind"}, 2
    if detected == "opportunity":
        report = verify_opportunity_evaluation_hash(result, expected=expected)
    else:
        report = verify_evaluation_hash(result, expected=expected)
    return report, 0 if report["valid"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verifica un evaluation_hash de CatedralX recomputándolo."
    )
    parser.add_argument("--input-file", required=True,
                        help="JSON con el objeto de evaluación (no un DecisionResult).")
    parser.add_argument("--kind", choices=("auto", "central", "opportunity"),
                        default="auto", help="Tipo de evaluación (por defecto: auto).")
    parser.add_argument("--expected", default=None,
                        help="Hash esperado (hex); si se omite se usa el embebido.")
    args = parser.parse_args(argv)
    report, code = verify_file(args.input_file, kind=args.kind, expected=args.expected)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
