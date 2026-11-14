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
    # Directories created by this writer are 0700 (mode only applies to
    # newly created directories; pre-existing ones such as /dev/shm are never
    # re-permissioned). The file itself is always 0600 (see below).
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    envelope: dict[str, Any] = {"PERCEIVE": data}
    try:
        # H-02: sign when a key is configured. Without a key the snapshot is
        # written unsigned and readers reject it fail-closed unless unsigned
        # mode was explicitly enabled for isolated tests.
        envelope = sign_snapshot_payload(envelope)
    except PermissionError:
        pass
    fd, tmp = tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(envelope, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
        os.chmod(target, 0o600)
        directory_fd = os.open(str(target.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise
    return target
