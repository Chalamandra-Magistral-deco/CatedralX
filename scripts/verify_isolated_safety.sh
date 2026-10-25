#!/usr/bin/env bash
# Reproducible, isolated verification for CatedralX. Does not deploy or use real market data.
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONDONTWRITEBYTECODE=1

printf '%s\n' '=== 1. TEST SUITE ==='
env -u CATEDRALX_PANIC_PATH \
    -u CATEDRALX_APPROVAL_SECRET \
    -u CATEDRALX_APPROVAL_DIR \
    -u CATEDRALX_STATE_PATH \
    -u CATEDRALX_SNAPSHOT_PATH \
    -u CATEDRALX_FEEDBACK_PATH \
    PYTHONPATH="$ROOT_DIR:$ROOT_DIR/elite" pytest -q -p no:cacheprovider

printf '\n%s\n' '=== 2. DIFF WHITESPACE CHECK ==='
git diff --check
printf '%s\n' 'git diff --check: OK'

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/catedralx-safety.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

printf '\n%s\n' '=== 3. SYNTHETIC ANALYSIS SMOKE TEST ==='
NORMAL="$TMP_ROOT/normal"
mkdir -p "$NORMAL"
python - "$NORMAL/snapshot.json" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

prices = [100.0 + index * 0.15 + ((index % 3) - 1) * 0.02 for index in range(30)]
payload = {
    "PERCEIVE": {
        "historial_precios": prices,
        "precio": prices[-1],
        "source": "synthetic-smoke-test",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "gap": 0.0,
        "inercia": 0.0,
    }
}
Path(sys.argv[1]).write_text(json.dumps(payload), encoding="utf-8")
PY
CATEDRALX_SNAPSHOT_PATH="$NORMAL/snapshot.json" \
CATEDRALX_STATE_PATH="$NORMAL/state/hormonas.json" \
CATEDRALX_FEEDBACK_PATH="$NORMAL/feedback.jsonl" \
CATEDRALX_PANIC_PATH="$NORMAL/defense/.panic" \
PYTHONPATH="$ROOT_DIR/elite" python "$ROOT_DIR/elite/REASON/razon.py" > "$NORMAL/result.json"
python - "$NORMAL/result.json" "$NORMAL/state/hormonas.json" "$NORMAL/feedback.jsonl" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert result.get("status") == "ANALYSIS_COMPLETE", result
assert result.get("trading_enabled") is False, result
assert result.get("orders_created") is False, result
assert result.get("orders_executed") is False, result
assert result.get("prediction_id"), result
assert Path(sys.argv[2]).is_file(), "Expected isolated state file"
assert Path(sys.argv[3]).is_file(), "Expected isolated feedback file"
print("Synthetic analysis: OK (trading disabled; no orders)")
PY

printf '\n%s\n' '=== 4. EMERGENCY-LOCK SMOKE TEST ==='
PANIC="$TMP_ROOT/panic"
mkdir -p "$PANIC/defense"
printf '%s\n' 'synthetic emergency test' > "$PANIC/defense/.panic"
set +e
CATEDRALX_SNAPSHOT_PATH="$PANIC/nonexistent-snapshot.json" \
CATEDRALX_STATE_PATH="$PANIC/state/hormonas.json" \
CATEDRALX_FEEDBACK_PATH="$PANIC/feedback.jsonl" \
CATEDRALX_PANIC_PATH="$PANIC/defense/.panic" \
PYTHONPATH="$ROOT_DIR/elite" python "$ROOT_DIR/elite/REASON/razon.py" > "$PANIC/result.json"
EXIT_CODE=$?
set -e
python - "$PANIC/result.json" "$PANIC/state/hormonas.json" "$PANIC/feedback.jsonl" "$EXIT_CODE" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert int(sys.argv[4]) == 2, f"Unexpected exit code: {sys.argv[4]}"
assert result.get("status") == "NO_CYCLE", result
assert "Bloqueo de emergencia activo" in result.get("reason", ""), result
assert result.get("trading_enabled") is False, result
assert result.get("orders_created") is False, result
assert result.get("orders_executed") is False, result
assert not Path(sys.argv[2]).exists(), "Blocked analysis must not persist state"
assert not Path(sys.argv[3]).exists(), "Blocked analysis must not record feedback"
print("Emergency lock: OK (cycle rejected; no state or feedback written)")
PY

printf '\n%s\n' 'ALL ISOLATED SAFETY CHECKS PASSED'
