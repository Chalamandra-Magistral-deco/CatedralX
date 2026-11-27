"""Durable append-only MSX ledger for virtual energy transactions.

Each line is canonical JSON with a SHA-256 hash chained to the previous line.
This is tamper-evident, not signed or an authorization mechanism. A malformed
or broken chain fails closed; the ledger is never silently reset.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback uses process-local lock
    fcntl = None

_THREAD_LOCK = threading.RLock()
_GENESIS = "0" * 64


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _ledger_path(path: str | os.PathLike[str] | None = None) -> Path:
    raw = path or os.getenv("CATEDRALX_ENERGY_LEDGER_PATH")
    if raw is None:
        raw = str(Path.home() / ".catedralx" / "energy-ledger.jsonl")
    return Path(raw).expanduser()


class EnergyLedger:
    """Hash-chained JSONL ledger with locked, fsynced appends and strict replay."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = _ledger_path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _locked(self):
        class Lock:
            def __init__(inner, owner): inner.owner = owner; inner.handle = None
            def __enter__(inner):
                _THREAD_LOCK.acquire()
                inner.owner.path.parent.mkdir(parents=True, exist_ok=True)
                inner.handle = inner.owner.lock_path.open("a+b")
                if fcntl is not None: fcntl.flock(inner.handle.fileno(), fcntl.LOCK_EX)
                return inner
            def __exit__(inner, exc_type, exc, tb):
                if inner.handle:
                    if fcntl is not None: fcntl.flock(inner.handle.fileno(), fcntl.LOCK_UN)
                    inner.handle.close()
                _THREAD_LOCK.release()
        return Lock(self)

    def read(self) -> list[dict[str, Any]]:
        with self._locked():
            return self._read_unlocked()

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists(): return []
        records = []
        previous = _GENESIS
        with self.path.open("rb") as stream:
            for number, raw in enumerate(stream, 1):
                if not raw.endswith(b"\n"):
                    raise ValueError(f"MSX energy ledger: línea {number} incompleta")
                try:
                    record = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(f"MSX energy ledger: JSON inválido en línea {number}") from exc
                if not isinstance(record, dict) or record.get("previous_hash") != previous:
                    raise ValueError(f"MSX energy ledger: cadena rota en línea {number}")
                digest = record.get("record_hash")
                payload = {key: value for key, value in record.items() if key != "record_hash"}
                actual = hashlib.sha256(_canonical(payload)).hexdigest()
                if digest != actual:
                    raise ValueError(f"MSX energy ledger: hash inválido en línea {number}")
                previous = digest
                records.append(record)
        return records

    def transact(self, builder):
        """Build and append while holding the ledger lock across replay and commit."""
        with self._locked():
            records = self._read_unlocked()
            transaction = builder(records)
            if not isinstance(transaction, dict): raise TypeError("builder debe devolver un dict")
            _canonical(transaction)
            txid = transaction.get("transaction_id")
            if not isinstance(txid, str) or not txid.strip(): raise ValueError("transaction_id requerido")
            if any(item.get("transaction_id") == txid for item in records): raise ValueError("transaction_id duplicado en MSX")
            previous = records[-1]["record_hash"] if records else _GENESIS
            payload = {**transaction, "sequence": len(records) + 1, "previous_hash": previous}
            record = {**payload, "record_hash": hashlib.sha256(_canonical(payload)).hexdigest()}
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                with os.fdopen(fd, "ab", closefd=False) as stream:
                    stream.write(_canonical(record) + b"\n"); stream.flush(); os.fsync(stream.fileno())
            finally: os.close(fd)
            return record
    def append(self, transaction: dict[str, Any]) -> dict[str, Any]:
        """Append one caller-built event using the same serialized transaction path."""
        return self.transact(lambda _records: transaction)
