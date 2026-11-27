"""CLI verification for one persisted CatedralX DecisionResult."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ELITE_DIR = ROOT / "elite"
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))

from contracts.result_store import verify_result_record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-id", required=True)
    parser.add_argument("--expected-file", required=True)
    args = parser.parse_args()
    try:
        expected = json.loads(Path(args.expected_file).read_text(encoding="utf-8"))
        report = verify_result_record(args.result_id, expected)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
