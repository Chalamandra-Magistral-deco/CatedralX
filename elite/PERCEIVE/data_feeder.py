"""Atomic snapshot writer. Callers must supply observed data."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .sensors import normalize_market_payload
from .snapshot_signing import sign_snapshot_payload


def snapshot_path() -> Path:
    return Path(os.environ.get("CATEDRALX_SNAPSHOT_PATH", "/dev/shm/cathedral_snapshot.json")).expanduser()


def write_observation(payload: dict[str, Any], path: str | Path | None = None) -> Path:
    data = normalize_market_payload(payload)
    target = Path(path).expanduser() if path else snapshot_path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    envelope: dict[str, Any] = {"PERCEIVE": data}
    try:
        envelope = sign_snapshot_payload(envelope)
    except PermissionError:
        # Preserve the documented unsigned-test path. Readers remain fail-closed
        # unless unsigned mode is explicitly enabled by their test environment.
        pass

    fd, temporary_name = tempfile.mkstemp(
        prefix=target.name + ".", dir=str(target.parent), text=True
    )
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(envelope, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory_fd = os.open(str(target.parent), directory_flags)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return target
