#!/usr/bin/env python3
"""One-shot event scanner: dispatch only fully authorized, not-yet-dispatched cycles.

Designed to be invoked by a timer or after an `authorize` ledger event. It never
creates authorization, moves money, places orders, or enables trading.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ELITE_DIR = Path(__file__).resolve().parents[1]
BIN_DIR = Path(__file__).resolve().parent
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from dispatch_agents import dispatch_task, load_authorized_proposal
from FEX.GOVERNANCE.economic_cycle import ledger_path as default_ledger_path
from FEX.GOVERNANCE.economic_cycle import resumir_ciclos

_AUTHORIZED_EVENTS = ["measure", "evaluate", "propose", "authorize"]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Dispatch ledger inválido en línea {line_number}") from exc
            if not isinstance(item, dict):
                raise TypeError(f"Dispatch ledger contiene un registro no-objeto en línea {line_number}")
            records.append(item)
    return records


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ) + "\n"
    with path.open("a", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def scan_and_dispatch(
    *,
    ledger: Path,
    dispatch_log: Path,
    api_url: str,
    secret: str,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Dispatch eligible cycles exactly once using a stable server idempotency key."""
    if not secret:
        raise ValueError("CHALAMANDRA_CATEDRALX_JWT_SECRET no está configurado")
    ledger = ledger.expanduser().resolve()
    dispatch_log = dispatch_log.expanduser().resolve()
    dispatch_log.parent.mkdir(parents=True, exist_ok=True)
    lock_path = dispatch_log.with_suffix(dispatch_log.suffix + ".lock")
    summary = resumir_ciclos(ledger)
    eligible = [
        row for row in summary["cycles"]
        if row.get("stage") == "authorize" and row.get("events") == _AUTHORIZED_EVENTS
    ]

    dispatched: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    with lock_path.open("a", encoding="utf-8") as lock_stream:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
        try:
            prior = _read_jsonl(dispatch_log)
            done = {
                str(row.get("cycle_id"))
                for row in prior
                if row.get("status") == "dispatched" and row.get("cycle_id")
            }
            for cycle in eligible:
                cycle_id = str(cycle["cycle_id"])
                if cycle_id in done:
                    continue
                idempotency_key = "catedralx-economic-cycle:" + cycle_id
                attempt_at = datetime.now(UTC).isoformat()
                try:
                    payload = load_authorized_proposal(ledger, cycle_id)
                    trace_id = payload.get("trace_id")
                    traceparent = (
                        f"00-{trace_id}-{secrets.token_hex(8)}-01"
                        if trace_id is not None else None
                    )
                    response = dispatch_task(
                        "catedralx_economic_proposal_review",
                        payload,
                        api_url,
                        secret,
                        timeout=timeout,
                        idempotency_key=idempotency_key,
                        traceparent=traceparent,
                    )
                    if not isinstance(response, dict) or not response.get("task_id") or not response.get("run_id"):
                        raise RuntimeError("La API no devolvió task_id y run_id válidos")
                    record = {
                        "schema_version": 1,
                        "recorded_at": datetime.now(UTC).isoformat(),
                        "cycle_id": cycle_id,
                        "idempotency_key": idempotency_key,
                        "status": "dispatched",
                        "api_status": response.get("status"),
                        "run_id": response["run_id"],
                        "task_id": response["task_id"],
                        "trace_id": response.get("trace_id"),
                    }
                    _append_jsonl(dispatch_log, record)
                    dispatched.append(record)
                    done.add(cycle_id)
                except (OSError, ValueError, TypeError, RuntimeError) as exc:
                    record = {
                        "schema_version": 1,
                        "recorded_at": attempt_at,
                        "cycle_id": cycle_id,
                        "idempotency_key": idempotency_key,
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:400],
                    }
                    _append_jsonl(dispatch_log, record)
                    errors.append({"cycle_id": cycle_id, "error_type": type(exc).__name__})
        finally:
            fcntl.flock(lock_stream.fileno(), fcntl.LOCK_UN)

    return {
        "eligible": len(eligible),
        "already_dispatched": max(0, len(eligible) - len(dispatched) - len(errors)),
        "dispatched": dispatched,
        "errors": errors,
        "read_only_ledger": True,
        "trading_enabled": False,
        "orders_created": False,
        "orders_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-path", type=Path, default=default_ledger_path())
    parser.add_argument(
        "--dispatch-log-path", type=Path,
        default=Path.home() / ".local/state/chalamandra/catedralx/dispatches.jsonl",
    )
    parser.add_argument(
        "--api-url", default=os.getenv("CHALAMANDRA_API_URL", "http://127.0.0.1:8766")
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    if not 0 < args.timeout <= 30:
        parser.error("--timeout debe estar entre 0 y 30 segundos")
    try:
        result = scan_and_dispatch(
            ledger=args.ledger_path,
            dispatch_log=args.dispatch_log_path,
            api_url=args.api_url,
            secret=os.getenv("CHALAMANDRA_CATEDRALX_JWT_SECRET", ""),
            timeout=args.timeout,
        )
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "error": str(exc)[:400]}))
        return 1
    print(json.dumps({"status": "ok", **result}, ensure_ascii=False, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
