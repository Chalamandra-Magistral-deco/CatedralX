"""Validate snapshot schema and market-observation freshness."""
from __future__ import annotations

import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .data_feeder import snapshot_path
from .snapshot_signing import (
    gap_inertia_in_range,
    is_allowed_source,
    snapshots_require_signature,
    verify_snapshot_signature,
)

DEFAULT_MAX_AGE_SECONDS = 120.0
FUTURE_CLOCK_TOLERANCE_SECONDS = 5.0


def validate_snapshot_payload(
    payload: object,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    now: float | None = None,
    *,
    require_signature: bool | None = None,
) -> dict[str, Any]:
    """Validate schema, observed market time, provenance and signature."""
    def rejected(reason: str, *, age=None, observed_at=None, has_prices=False):
        return {
            "healthy": False, "reason": reason, "age_seconds": age,
            "observed_at": observed_at, "has_prices": has_prices,
            "max_age_seconds": max_age_seconds,
        }

    try:
        if isinstance(max_age_seconds, bool):
            return rejected("invalid_time_configuration")
        max_age = float(max_age_seconds)
        current = time.time() if now is None else float(now)
    except (TypeError, ValueError, OverflowError):
        return rejected("invalid_time_configuration")
    if not math.isfinite(current) or not math.isfinite(max_age) or max_age <= 0:
        return rejected("invalid_time_configuration")

    signature_required = snapshots_require_signature() if require_signature is None else require_signature
    if not isinstance(signature_required, bool):
        return rejected("invalid_signature_configuration")
    if not isinstance(payload, dict):
        return rejected("invalid_snapshot_schema")
    perceive = payload.get("PERCEIVE")
    if not isinstance(perceive, dict):
        return rejected("missing_perceive_section")

    prices = perceive.get("historial_precios")
    if not isinstance(prices, list) or len(prices) < 30:
        return rejected("insufficient_price_history")
    try:
        normalized = []
        for price in prices:
            if isinstance(price, bool):
                raise ValueError
            value = float(price)
            if not math.isfinite(value) or value <= 0:
                raise ValueError
            normalized.append(value)
        latest_value = perceive.get("precio", prices[-1])
        if isinstance(latest_value, bool):
            raise ValueError
        latest = float(latest_value)
        if not math.isfinite(latest) or latest <= 0:
            raise ValueError
        if not math.isclose(latest, normalized[-1], rel_tol=1e-12, abs_tol=0.0):
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        return rejected("invalid_price_history", has_prices=True)

    observed_at = perceive.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at.strip():
        return rejected("missing_observed_at", has_prices=True)
    try:
        parsed = datetime.fromisoformat(observed_at.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return rejected("observed_at_requires_timezone", observed_at=observed_at, has_prices=True)
        age = current - parsed.timestamp()
    except (ValueError, TypeError, OverflowError, OSError):
        return rejected("invalid_observed_at", observed_at=observed_at, has_prices=True)

    if age < -FUTURE_CLOCK_TOLERANCE_SECONDS:
        return rejected("observation_from_future", age=age, observed_at=observed_at, has_prices=True)
    age = max(0.0, age)
    if age > max_age:
        return rejected("stale_observation", age=age, observed_at=observed_at, has_prices=True)

    for field in ("gap", "inercia"):
        if field in perceive and not gap_inertia_in_range(perceive[field]):
            return rejected("gap_or_inertia_out_of_range", age=age, observed_at=observed_at, has_prices=True)

    source = perceive.get("source", "unspecified")
    if signature_required:
        if not is_allowed_source(source):
            return rejected("snapshot_source_not_allowed", age=age, observed_at=observed_at, has_prices=True)
        signature_ok, signature_status = verify_snapshot_signature(payload)
        if not signature_ok:
            reason = "snapshot_signature_missing" if signature_status == "missing" else "snapshot_signature_invalid"
            return rejected(reason, age=age, observed_at=observed_at, has_prices=True)
        signature_status = "verified"
    else:
        signature_status = "not_required"

    return {
        "healthy": True, "reason": "ok", "age_seconds": age,
        "observed_at": observed_at, "has_prices": True,
        "max_age_seconds": max_age, "source": source,
        "signature": signature_status,
    }


def check_snapshot(
    path: str | Path | None = None,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    now: float | None = None,
    *,
    require_signature: bool | None = None,
) -> dict[str, Any]:
    """Read and validate the snapshot using market time, not file mtime."""
    target = Path(path).expanduser() if path else snapshot_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"healthy": False, "reason": "snapshot_not_found", "exists": False,
                "age_seconds": None, "has_prices": False, "path": str(target)}
    except (OSError, ValueError, TypeError):
        return {"healthy": False, "reason": "snapshot_unreadable", "exists": target.exists(),
                "age_seconds": None, "has_prices": False, "path": str(target)}
    result = validate_snapshot_payload(payload, max_age_seconds, now, require_signature=require_signature)
    result["exists"] = True
    result["path"] = str(target)
    return result
