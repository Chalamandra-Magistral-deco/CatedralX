"""HMAC signing and provenance verification for RSX snapshots (H-02).

The canonical cycle must never trust prices from an unsigned file: any local
process can rewrite ``/dev/shm/cathedral_snapshot.json``. This module signs
the ``PERCEIVE`` section of a snapshot with HMAC-SHA256 (same keyring pattern
as ``DSX/DEFENSE/guards.py``: versioned keyring with a legacy-secret fallback,
keys of at least 32 bytes) and verifies it on read.

Signature envelope (top level of the snapshot JSON)::

    {"PERCEIVE": {...}, "signature": {"key_id": "...", "alg": "HMAC-SHA256",
                                      "signature": "<hex>"}}

The HMAC covers the canonical JSON of the whole ``PERCEIVE`` section, so it
binds prices, ``source``, ``observed_at``, ``gap`` and ``inercia`` together.
Replay is bounded by the snapshot freshness check itself (max 120 s): a
signed snapshot older than that is rejected as stale even if its signature
is valid.

Unsigned snapshots are rejected fail-closed unless the caller explicitly
opts into unsigned mode with ``CATEDRALX_SNAPSHOT_ALLOW_UNSIGNED=true``.
That flag exists only for isolated tests (``scripts/verify_isolated_safety.sh``
writes synthetic snapshots with no key); it must never be set in production.

``source`` is validated against an allowlist: the only production source is
the public Binance spot feed (``binance_spot_public:<SYMBOL>:1m``); the only
other accepted value is the documented isolated-test marker
``synthetic-smoke-test``. In unsigned mode the provenance check is skipped
as a whole, because unsigned mode already declares "no provenance".

``gap``/``inercia`` are 1-minute return features (see
``PERCEIVE/stream_altar.py::build_observation_from_klines``: ``open/prev-1``
and ``close/prev-1``), so by definition they live in [-1, 1]. Values outside
that range are inconsistent with their definition and are rejected.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import math
import os
import re
from typing import Any

SNAPSHOT_SIGNING_SECRET_ENV = "CATEDRALX_SNAPSHOT_SIGNING_SECRET"
SNAPSHOT_KEYRING_ENV = "CATEDRALX_SNAPSHOT_KEYRING"
SNAPSHOT_ACTIVE_KEY_ID_ENV = "CATEDRALX_SNAPSHOT_ACTIVE_KEY_ID"
SNAPSHOT_ALLOW_UNSIGNED_ENV = "CATEDRALX_SNAPSHOT_ALLOW_UNSIGNED"

SIGNATURE_ALG = "HMAC-SHA256"
_MIN_KEY_BYTES = 32

# Production market source: public Binance spot 1-minute closed candles.
_ALLOWED_SOURCE_RE = re.compile(r"^binance_spot_public:[A-Z0-9]{5,20}:1m$")
# Documented isolated-test marker (verify_isolated_safety.sh). Never a feed.
ALLOWED_SOURCES = frozenset({"synthetic-smoke-test"})

# gap/inercia are 1-minute returns by definition; see module docstring.
GAP_INERTIA_MIN = -1.0
GAP_INERTIA_MAX = 1.0

_UNSIGNED_TRUE_VALUES = {"1", "true", "yes", "on"}


def snapshots_require_signature() -> bool:
    """True unless unsigned mode was explicitly enabled (isolated tests only)."""
    return (
        os.environ.get(SNAPSHOT_ALLOW_UNSIGNED_ENV, "").strip().lower()
        not in _UNSIGNED_TRUE_VALUES
    )


def is_allowed_source(source: Any) -> bool:
    """Check a snapshot source against the provenance allowlist."""
    if not isinstance(source, str):
        return False
    return source in ALLOWED_SOURCES or bool(_ALLOWED_SOURCE_RE.fullmatch(source))


def gap_inertia_in_range(value: Any) -> bool:
    """Check a gap/inercia feature is a finite 1-minute return in [-1, 1]."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(number) and GAP_INERTIA_MIN <= number <= GAP_INERTIA_MAX


def _snapshot_keyring() -> tuple[str, dict[str, bytes]]:
    """Load a versioned signing keyring; active key signs, all keys verify."""
    raw_ring = os.environ.get(SNAPSHOT_KEYRING_ENV, "")
    active_id = os.environ.get(SNAPSHOT_ACTIVE_KEY_ID_ENV, "")
    if raw_ring:
        try:
            parsed = json.loads(raw_ring)
        except (TypeError, ValueError) as exc:
            raise PermissionError(
                "Keyring de firma de snapshot inválido; firma bloqueada"
            ) from exc
        if not isinstance(parsed, dict) or not active_id or active_id not in parsed:
            raise PermissionError(
                "Keyring de firma de snapshot sin clave activa válida; firma bloqueada"
            )
        keys: dict[str, bytes] = {}
        for key_id, secret in parsed.items():
            if (
                not isinstance(key_id, str)
                or not key_id
                or not isinstance(secret, str)
                or len(secret.encode("utf-8")) < _MIN_KEY_BYTES
            ):
                raise PermissionError(
                    "Keyring de firma de snapshot contiene clave inválida; firma bloqueada"
                )
            keys[key_id] = secret.encode("utf-8")
        return active_id, keys
    legacy = os.environ.get(SNAPSHOT_SIGNING_SECRET_ENV, "").encode("utf-8")
    if len(legacy) < _MIN_KEY_BYTES:
        raise PermissionError(
            "Firma de snapshot bloqueada: configure keyring versionado o "
            "CATEDRALX_SNAPSHOT_SIGNING_SECRET con al menos 32 bytes"
        )
    return "legacy", {"legacy": legacy}


def _snapshot_key(key_id: str | None = None) -> bytes:
    active_id, keys = _snapshot_keyring()
    selected = active_id if key_id is None else key_id
    if selected not in keys:
        raise PermissionError(
            "Clave de firma de snapshot desconocida o retirada; verificación bloqueada"
        )
    return keys[selected]


def _canonical_perceive(perceive: dict[str, Any]) -> bytes:
    return json.dumps(
        perceive, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sign_snapshot_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``payload`` with a top-level HMAC signature added.

    Raises ``PermissionError`` when no signing key is configured and
    ``ValueError`` when the payload has no ``PERCEIVE`` object to sign.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("PERCEIVE"), dict):
        raise TypeError("snapshot sin sección PERCEIVE; no se puede firmar")
    active_key_id, _ = _snapshot_keyring()
    key = _snapshot_key(active_key_id)
    signature = hmac.new(
        key, _canonical_perceive(payload["PERCEIVE"]), hashlib.sha256
    ).hexdigest()
    signed = copy.deepcopy(payload)
    signed["signature"] = {
        "key_id": active_key_id,
        "alg": SIGNATURE_ALG,
        "signature": signature,
    }
    return signed


def verify_snapshot_signature(payload: dict[str, Any]) -> tuple[bool, str]:
    """Verify a snapshot signature.

    Returns ``(ok, status)`` with status in ``verified`` | ``missing`` |
    ``invalid`` | ``malformed`` | ``key_unavailable``. Never raises for a
    bad payload: any verification failure is a plain ``False`` so callers
    can fail closed with a reason code.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("PERCEIVE"), dict):
        return False, "malformed"
    envelope = payload.get("signature")
    if envelope is None:
        return False, "missing"
    if not isinstance(envelope, dict):
        return False, "malformed"
    if envelope.get("alg") != SIGNATURE_ALG:
        return False, "malformed"
    key_id = envelope.get("key_id")
    signature = envelope.get("signature")
    if not isinstance(key_id, str) or not key_id:
        return False, "malformed"
    if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{64}", signature):
        return False, "invalid"
    try:
        expected = hmac.new(
            _snapshot_key(key_id), _canonical_perceive(payload["PERCEIVE"]), hashlib.sha256
        ).hexdigest()
    except PermissionError:
        return False, "key_unavailable"
    except (TypeError, ValueError):
        return False, "malformed"
    if not hmac.compare_digest(signature, expected):
        return False, "invalid"
    return True, "verified"
