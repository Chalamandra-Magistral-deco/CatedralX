"""H-03: hormonal state integrity (hash/firma + flock + fsync + 0600).

Fail-closed on corrupt JSON or on a present-but-invalid integrity
envelope; legacy files without an envelope are accepted once (migration)
and re-signed on the next save.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import pytest
from REASON.procesador import ProcesadorEndocrino, migrar_estado_legacy

SECRET = "test-only-hormonal-state-hmac-key-32-bytes"


@pytest.fixture(autouse=True)
def _hormonal_key(monkeypatch):
    monkeypatch.setenv("CATEDRALX_HORMONAS_HMAC_KEY", SECRET)
    monkeypatch.delenv("CATEDRALX_HORMONAS_KEYRING", raising=False)
    monkeypatch.delenv("CATEDRALX_HORMONAS_ACTIVE_KEY_ID", raising=False)


def test_guardar_signs_state_and_sets_0600(tmp_path):
    target = tmp_path / "state" / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    data = proc.guardar()
    assert "integrity" in data
    assert data["integrity"]["alg"] == "HMAC-SHA256"
    assert (os.stat(target).st_mode & 0o777) == 0o600
    assert (os.stat(target.parent).st_mode & 0o777) == 0o700
    assert datetime.fromisoformat(data["timestamp"]).tzinfo is not None
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert stored == data


def test_reload_verifies_signature_and_restores_concentrations(tmp_path):
    target = tmp_path / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    proc.conc["cortisol_C"] = 0.77
    proc.guardar()
    reloaded = ProcesadorEndocrino(output_path=target)
    assert reloaded.conc["cortisol_C"] == pytest.approx(0.77)


def test_tampered_state_fails_closed_on_load(tmp_path):
    target = tmp_path / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    proc.conc["dopamina_D"] = 0.11
    proc.guardar()
    stored = json.loads(target.read_text(encoding="utf-8"))
    stored["concentracion_actual"]["dopamina_D"] = 0.99
    target.write_text(json.dumps(stored), encoding="utf-8")
    with pytest.raises(ValueError, match="integridad inválida"):
        ProcesadorEndocrino(output_path=target)


def test_corrupt_json_fails_closed_on_load(tmp_path):
    target = tmp_path / "hormonas.json"
    target.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupto"):
        ProcesadorEndocrino(output_path=target)


def test_non_object_state_fails_closed_on_load(tmp_path):
    target = tmp_path / "hormonas.json"
    target.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupto"):
        ProcesadorEndocrino(output_path=target)


def test_missing_file_still_loads_defaults(tmp_path):
    target = tmp_path / "missing" / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    assert proc.conc["cortisol_C"] == pytest.approx(0.30)
    assert proc.conc["dopamina_D"] == pytest.approx(0.60)


def test_unsigned_legacy_state_is_rejected_until_explicit_migration(tmp_path):
    target = tmp_path / "hormonas.json"
    legacy = {
        "timestamp": "2026-11-14T00:00:00+00:00",
        "concentracion_actual": {
            "oxitocina_O": 0.45, "dopamina_D": 0.60, "serotonina_S": 0.50,
            "cortisol_C": 0.30, "adrenalina_A": 0.40, "melatonina_M": 0.20,
        },
        "estres_critico": False,
        "contexto": {"market_phase": "desconocido"},
        "economic_feedback": {},
    }
    original = json.dumps(legacy).encode("utf-8")
    target.write_bytes(original)
    with pytest.raises(ValueError, match="estado sin firma"):
        ProcesadorEndocrino(output_path=target)

    backup = migrar_estado_legacy(output_path=target)
    assert backup.read_bytes() == original
    signed = json.loads(target.read_text(encoding="utf-8"))
    assert "integrity" in signed
    assert ProcesadorEndocrino(output_path=target).conc["cortisol_C"] == pytest.approx(0.30)


def test_legacy_migration_refuses_to_overwrite_existing_backup(tmp_path):
    target = tmp_path / "hormonas.json"
    legacy = {
        "concentracion_actual": {
            "oxitocina_O": 0.45, "dopamina_D": 0.60, "serotonina_S": 0.50,
            "cortisol_C": 0.30, "adrenalina_A": 0.40, "melatonina_M": 0.20,
        },
        "contexto": {},
    }
    target.write_text(json.dumps(legacy), encoding="utf-8")
    backup = target.with_name(target.name + ".legacy.bak")
    backup.write_text("preserved", encoding="utf-8")
    with pytest.raises(FileExistsError):
        migrar_estado_legacy(output_path=target)
    assert backup.read_text(encoding="utf-8") == "preserved"
    assert "integrity" not in json.loads(target.read_text(encoding="utf-8"))


def test_state_signed_with_retired_key_fails_closed(tmp_path, monkeypatch):
    import json as _json

    target = tmp_path / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    proc.guardar()
    monkeypatch.setenv(
        "CATEDRALX_HORMONAS_KEYRING",
        _json.dumps({"k-new": "test-only-other-hormonal-key-32-bytes"}),
    )
    monkeypatch.setenv("CATEDRALX_HORMONAS_ACTIVE_KEY_ID", "k-new")
    monkeypatch.delenv("CATEDRALX_HORMONAS_HMAC_KEY", raising=False)
    with pytest.raises(ValueError, match="no se puede verificar"):
        ProcesadorEndocrino(output_path=target)


def test_guardar_without_key_fails_closed_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("CATEDRALX_HORMONAS_HMAC_KEY", raising=False)
    monkeypatch.delenv("CATEDRALX_HORMONAS_KEYRING", raising=False)
    monkeypatch.delenv("CATEDRALX_HORMONAS_ACTIVE_KEY_ID", raising=False)
    target = tmp_path / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    with pytest.raises(PermissionError, match="Firma de hormonas bloqueada"):
        proc.guardar()
    assert not target.exists()


def test_removing_integrity_from_signed_state_is_rejected(tmp_path):
    target = tmp_path / "hormonas.json"
    proc = ProcesadorEndocrino(output_path=target)
    proc.guardar()
    stored = json.loads(target.read_text(encoding="utf-8"))
    del stored["integrity"]
    target.write_text(json.dumps(stored), encoding="utf-8")
    with pytest.raises(ValueError, match="estado sin firma"):
        ProcesadorEndocrino(output_path=target)


def test_concurrent_saves_keep_a_valid_signed_state(tmp_path):
    import threading

    target = tmp_path / "hormonas.json"
    errors: list[BaseException] = []

    def save(value: float) -> None:
        try:
            proc = ProcesadorEndocrino(output_path=target)
            proc.conc["cortisol_C"] = value
            proc.guardar()
        except BaseException as exc:  # noqa: BLE001 - collected by the test
            errors.append(exc)

    threads = [threading.Thread(target=save, args=(0.1 * i,)) for i in range(1, 9)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert "integrity" in stored
    assert ProcesadorEndocrino(output_path=target).conc["cortisol_C"] == pytest.approx(
        stored["concentracion_actual"]["cortisol_C"]
    )
