#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONDONTWRITEBYTECODE=1

# Seleccionar el intérprete que ejecuta pytest.
PYTHON_BIN="${CATEDRALX_PYTHON:-}"

if [[ -z "$PYTHON_BIN" ]]; then
    PYTEST_BIN="$(command -v pytest || true)"
    if [[ -n "$PYTEST_BIN" ]]; then
        SHEBANG="$(head -n 1 "$PYTEST_BIN")"
        CANDIDATE="${SHEBANG#\#!}"
        [[ -x "$CANDIDATE" ]] && PYTHON_BIN="$CANDIDATE"
    fi
fi

if [[ -z "$PYTHON_BIN" && -x /datos/venvs/global/bin/python ]]; then
    PYTHON_BIN="/datos/venvs/global/bin/python"
fi

if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    echo "ERROR: intérprete Python no disponible" >&2
    exit 1
fi

"$PYTHON_BIN" -c 'import numpy' || {
    echo "ERROR: NumPy no disponible en el intérprete seleccionado" >&2
    exit 1
}

export CATEDRALX_PYTHON="$PYTHON_BIN"
echo "PYTHON: $PYTHON_BIN"
"$PYTHON_BIN" --version

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/catedralx-safety.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

echo
echo "========== 1. TEST SUITE =========="

env \
    -u CATEDRALX_PANIC_PATH \
    -u CATEDRALX_APPROVAL_SECRET \
    -u CATEDRALX_APPROVAL_DIR \
    -u CATEDRALX_STATE_PATH \
    -u CATEDRALX_SNAPSHOT_PATH \
    -u CATEDRALX_FEEDBACK_PATH \
    -u CATEDRALX_RESULT_STORE_PATH \
    CATEDRALX_RESULT_STORE_PATH="$TMP_ROOT/test-suite-results.jsonl" \
    PYTHONPATH="$ROOT_DIR:$ROOT_DIR/elite" \
    "$PYTHON_BIN" -m pytest -q -p no:cacheprovider

echo
echo "========== 2. DIFF CHECK =========="
git diff --check

echo
echo "========== 3. ANALISIS SINTETICO =========="

NORMAL="$TMP_ROOT/normal"
mkdir -p "$NORMAL"

"$PYTHON_BIN" - "$NORMAL/snapshot.json" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

prices = [
    100.0 + i * 0.15 + ((i % 3) - 1) * 0.02
    for i in range(30)
]
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
CATEDRALX_RESULT_STORE_PATH="$NORMAL/results.jsonl" \
CATEDRALX_PANIC_PATH="$NORMAL/defense/.panic" \
PYTHONPATH="$ROOT_DIR/elite" \
"$PYTHON_BIN" "$ROOT_DIR/elite/REASON/razon.py" \
    > "$NORMAL/result.json"

"$PYTHON_BIN" - \
    "$NORMAL/result.json" \
    "$NORMAL/state/hormonas.json" \
    "$NORMAL/feedback.jsonl" \
    "$NORMAL/results.jsonl" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert result.get("status") == "ANALYSIS_COMPLETE", result
assert result.get("trading_enabled") is False, result
assert result.get("orders_created") is False, result
assert result.get("orders_executed") is False, result
assert result.get("prediction_id"), result

assert Path(sys.argv[2]).is_file(), "Falta el estado aislado"
assert Path(sys.argv[3]).is_file(), "Falta el feedback aislado"

decision = result.get("decision_result")
assert isinstance(decision, dict), "decision_result ausente"
assert decision.get("evidence"), decision
assert decision.get("provenance"), decision
assert len(str(decision.get("evaluation_hash") or "")) == 64, decision
assert decision.get("analysis_only") is True, decision
assert decision.get("orders_created") is False, decision
assert decision.get("orders_executed") is False, decision

store = Path(sys.argv[4])
assert store.is_file(), "No se creó el almacén aislado"

records = [
    json.loads(line)
    for line in store.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
assert len(records) == 1, records
assert records[0] == decision, "Salida CLI y persistencia son diferentes"

print(
    "ANALISIS OK:",
    f"evidence={len(decision['evidence'])}",
    f"provenance={len(decision['provenance'])}",
    "persistencia coincidente",
    "órdenes deshabilitadas",
)
PY

echo
echo "========== 4. BLOQUEO DE EMERGENCIA =========="

PANIC="$TMP_ROOT/panic"
mkdir -p "$PANIC/defense"
printf '%s\n' 'synthetic emergency test' > "$PANIC/defense/.panic"

set +e
CATEDRALX_SNAPSHOT_PATH="$PANIC/nonexistent-snapshot.json" \
CATEDRALX_STATE_PATH="$PANIC/state/hormonas.json" \
CATEDRALX_FEEDBACK_PATH="$PANIC/feedback.jsonl" \
CATEDRALX_RESULT_STORE_PATH="$PANIC/results.jsonl" \
CATEDRALX_PANIC_PATH="$PANIC/defense/.panic" \
PYTHONPATH="$ROOT_DIR/elite" \
"$PYTHON_BIN" "$ROOT_DIR/elite/REASON/razon.py" \
    > "$PANIC/result.json"
EXIT_CODE=$?
set -e

"$PYTHON_BIN" - \
    "$PANIC/result.json" \
    "$PANIC/state/hormonas.json" \
    "$PANIC/feedback.jsonl" \
    "$EXIT_CODE" \
    "$PANIC/results.jsonl" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert int(sys.argv[4]) == 2, sys.argv[4]
assert result.get("status") == "NO_CYCLE", result
assert "Bloqueo de emergencia activo" in result.get("reason", ""), result
assert result.get("trading_enabled") is False, result
assert result.get("orders_created") is False, result
assert result.get("orders_executed") is False, result

assert not Path(sys.argv[2]).exists(), "Se escribió estado durante el bloqueo"
assert not Path(sys.argv[3]).exists(), "Se escribió feedback durante el bloqueo"
assert not Path(sys.argv[5]).exists(), "Se persistió un resultado durante el bloqueo"

print("EMERGENCY LOCK OK: sin estado, feedback ni DecisionResult")
PY

echo
echo "ALL ISOLATED SAFETY CHECKS PASSED"
