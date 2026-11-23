from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from elite.MSX.cycle_manifest import (
    CicloManifest,
    construir_manifiesto_desde_ciclo,
    verificar_firma_manifest,
)
from elite.MSX.provenance import calcular_hash_conjunto


def _timestamps():
    start = datetime.now(UTC)
    return start.isoformat(), (start + timedelta(seconds=1)).isoformat()


def _manifest(**overrides):
    start, end = _timestamps()
    values = {
        "ciclo_id": "cycle-001",
        "timestamp_inicio": start,
        "timestamp_cierre": end,
        "snapshot_origen": "a" * 64,
        "conclusion_reason": "completed",
        "intencion_aex": {"action": "hold", "approved": False},
        "observacion_fex": {"status": "observed"},
        "huellas_modulos": {"SCX": "b" * 64},
    }
    values.update(overrides)
    return CicloManifest(**values)


def test_canonical_hash_is_stable_for_mapping_key_order():
    assert calcular_hash_conjunto({"b": 2, "a": 1}) == calcular_hash_conjunto({"a": 1, "b": 2})


def test_manifest_copies_input_mappings_and_returns_detached_payload():
    intent = {"action": "hold", "nested": {"value": 1}}
    manifest = _manifest(intencion_aex=intent)
    intent["nested"]["value"] = 99
    returned = manifest.generar_manifest()
    returned["intencion_aex"]["nested"]["value"] = 42
    assert manifest.generar_manifest()["intencion_aex"]["nested"]["value"] == 1


def test_manifest_hash_changes_only_with_payload():
    manifest = _manifest()
    assert manifest.hash_final() == calcular_hash_conjunto(manifest.generar_manifest())


def test_seal_is_idempotent_and_freezes_object():
    manifest = _manifest()
    sealed = manifest.sellar()
    assert manifest.sellar() == sealed
    with pytest.raises(AttributeError):
        manifest._payload = {}
    assert sealed["signature_status"] == "UNSIGNED"
    assert sealed["signature"] is None


def test_signed_manifest_verifies_and_detects_tampering():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    sealed = _manifest().sellar(private_key, key_id="test-key-1")
    assert verificar_firma_manifest(sealed, public_key) is True
    tampered = dict(sealed)
    tampered["conclusion_reason"] = "changed"
    assert verificar_firma_manifest(tampered, public_key) is False


def test_signed_manifest_requires_key_id():
    with pytest.raises(ValueError, match="key_id"):
        _manifest().sellar(Ed25519PrivateKey.generate())


def test_builder_requires_real_start_timestamp():
    with pytest.raises(ValueError, match="timestamp_inicio"):
        construir_manifiesto_desde_ciclo("cycle-002", {"conclusion": "done"})


def test_builder_uses_supplied_close_timestamp_and_cycle_data():
    start, end = _timestamps()
    manifest = construir_manifiesto_desde_ciclo(
        "cycle-003",
        {
            "timestamp_inicio": start,
            "timestamp_cierre": end,
            "snapshot_hash": "c" * 64,
            "conclusion": "completed",
            "intencion": {"action": "hold"},
            "huellas": {"SCX": "d" * 64},
        },
    )
    payload = manifest.generar_manifest()
    assert payload["timestamp_cierre"] == end
    assert payload["snapshot_origen"] == "c" * 64
    assert payload["intencion_aex"] == {"action": "hold"}
