"""H-02: snapshots must be HMAC-signed with a provenance-allowed source.

Adversarial cases: unsigned snapshot -> rejected; tampered price/source
after signing -> rejected; wrong key -> rejected; unknown key_id ->
rejected; gap/inercia outside [-1, 1] -> rejected. The explicit unsigned
mode exists only for isolated tests and must be opt-in.
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import pytest
from PERCEIVE.api_pulse import check_snapshot, validate_snapshot_payload
from PERCEIVE.data_feeder import write_observation
from PERCEIVE.snapshot_signing import sign_snapshot_payload

SECRET = "test-only-snapshot-signing-secret-32-bytes"
OTHER_SECRET = "test-only-other-snapshot-signing-secret"


def make_payload(*, source="binance_spot_public:BTCUSDT:1m", gap=0.0, inercia=0.0):
    prices = [100.0 + i * 0.15 for i in range(30)]
    payload = {
        "PERCEIVE": {
            "historial_precios": prices,
            "precio": prices[-1],
            "source": source,
            "observed_at": datetime.now(UTC).isoformat(),
            "gap": gap,
            "inercia": inercia,
        }
    }
    return payload


@pytest.fixture(autouse=True)
def _signing_key(monkeypatch):
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_SIGNING_SECRET", SECRET)
    monkeypatch.delenv("CATEDRALX_SNAPSHOT_ALLOW_UNSIGNED", raising=False)
    monkeypatch.delenv("CATEDRALX_SNAPSHOT_KEYRING", raising=False)


def test_signed_snapshot_from_allowed_source_is_healthy():
    result = validate_snapshot_payload(sign_snapshot_payload(make_payload()))
    assert result["healthy"] is True
    assert result["reason"] == "ok"
    assert result["signature"] == "verified"
    assert result["source"] == "binance_spot_public:BTCUSDT:1m"


def test_unsigned_snapshot_is_rejected_fail_closed():
    result = validate_snapshot_payload(make_payload())
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_missing"


def test_unsigned_snapshot_is_rejected_by_check_snapshot(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(make_payload()), encoding="utf-8")
    result = check_snapshot(path)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_missing"


def test_tampered_price_after_signing_is_rejected():
    signed = sign_snapshot_payload(make_payload())
    signed["PERCEIVE"]["historial_precios"][-1] = 99999.0
    signed["PERCEIVE"]["precio"] = 99999.0
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_invalid"


def test_tampered_source_after_signing_is_rejected():
    signed = sign_snapshot_payload(make_payload())
    signed["PERCEIVE"]["source"] = "binance_spot_public:ETHUSDT:1m"
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_invalid"


def test_source_outside_allowlist_is_rejected_even_when_signed():
    signed = sign_snapshot_payload(make_payload(source="evil-feed"))
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_source_not_allowed"


def test_unspecified_source_is_rejected_even_when_signed():
    signed = sign_snapshot_payload(make_payload(source="unspecified"))
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_source_not_allowed"


def test_signature_with_wrong_key_is_rejected(monkeypatch):
    signed = sign_snapshot_payload(make_payload())
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_SIGNING_SECRET", OTHER_SECRET)
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_invalid"


def test_signature_with_unknown_key_id_is_rejected():
    signed = sign_snapshot_payload(make_payload())
    signed["signature"]["key_id"] = "retired-key"
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_invalid"


def test_malformed_signature_envelope_is_rejected():
    signed = sign_snapshot_payload(make_payload())
    signed["signature"] = "not-an-envelope"
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_invalid"


def test_explicit_unsigned_mode_accepts_synthetic_snapshot(monkeypatch):
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_ALLOW_UNSIGNED", "true")
    result = validate_snapshot_payload(make_payload(source="synthetic-smoke-test"))
    assert result["healthy"] is True
    assert result["signature"] == "not_required"


def test_unsigned_mode_is_off_by_default(monkeypatch):
    monkeypatch.delenv("CATEDRALX_SNAPSHOT_ALLOW_UNSIGNED", raising=False)
    result = validate_snapshot_payload(make_payload())
    assert result["healthy"] is False
    assert result["reason"] == "snapshot_signature_missing"


def test_gap_out_of_range_is_rejected_even_when_signed():
    signed = sign_snapshot_payload(make_payload(gap=2.5))
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "gap_or_inertia_out_of_range"


def test_inercia_out_of_range_is_rejected_even_when_signed():
    signed = sign_snapshot_payload(make_payload(inercia=-1.5))
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is False
    assert result["reason"] == "gap_or_inertia_out_of_range"


def test_gap_inercia_at_definition_bounds_are_accepted():
    signed = sign_snapshot_payload(make_payload(gap=1.0, inercia=-1.0))
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is True


def test_key_rotation_overlap_key_verifies_old_signature(monkeypatch):
    import json as _json

    signed = sign_snapshot_payload(make_payload())
    ring = _json.dumps({"k-old": SECRET, "k-new": OTHER_SECRET})
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_KEYRING", ring)
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_ACTIVE_KEY_ID", "k-new")
    monkeypatch.delenv("CATEDRALX_SNAPSHOT_SIGNING_SECRET", raising=False)
    # Old signature was made with the legacy key id, which is not in the
    # ring: rotation retires it, so verification must fail closed.
    assert validate_snapshot_payload(signed)["healthy"] is False


def test_keyring_signs_with_active_key_and_verifies(monkeypatch):
    import json as _json

    ring = _json.dumps({"k1": SECRET, "k2": OTHER_SECRET})
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_KEYRING", ring)
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_ACTIVE_KEY_ID", "k2")
    monkeypatch.delenv("CATEDRALX_SNAPSHOT_SIGNING_SECRET", raising=False)
    signed = sign_snapshot_payload(make_payload())
    assert signed["signature"]["key_id"] == "k2"
    result = validate_snapshot_payload(signed)
    assert result["healthy"] is True
    assert result["signature"] == "verified"


def test_write_observation_signs_and_sets_0600_when_key_configured(tmp_path):
    target = tmp_path / "nested" / "snapshot.json"
    written = write_observation(make_payload()["PERCEIVE"], path=target)
    assert written == target
    assert (os.stat(written).st_mode & 0o777) == 0o600
    assert (os.stat(target.parent).st_mode & 0o777) == 0o700
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert stored["signature"]["alg"] == "HMAC-SHA256"
    assert validate_snapshot_payload(stored)["healthy"] is True


def test_write_observation_without_key_writes_unsigned_and_reader_rejects(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("CATEDRALX_SNAPSHOT_SIGNING_SECRET", raising=False)
    target = tmp_path / "snapshot.json"
    write_observation(make_payload()["PERCEIVE"], path=target)
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert "signature" not in stored
    assert validate_snapshot_payload(stored)["reason"] == "snapshot_signature_missing"


def test_short_signing_secret_fails_closed_on_sign(monkeypatch):
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_SIGNING_SECRET", "too-short")
    with pytest.raises(PermissionError):
        sign_snapshot_payload(make_payload())


def test_canonical_cycle_rejects_unsigned_snapshot(tmp_path, monkeypatch, capsys):
    from REASON import razon

    snapshot_path = tmp_path / "unsigned.json"
    snapshot_path.write_text(json.dumps(make_payload()), encoding="utf-8")
    monkeypatch.setenv("CATEDRALX_SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setattr(
        razon,
        "execute_cycle",
        lambda *_args, **_kwargs: pytest.fail("cycle must not run on unsigned data"),
    )
    assert razon.main() == 2
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "NO_CYCLE"
    assert "snapshot_signature_missing" in output["reason"]
    assert output["trading_enabled"] is False
    assert output["orders_executed"] is False
