from __future__ import annotations

import pytest
from FEX.GOVERNANCE.sustainability import (
    CONTINUE,
    DYNAMIC_BRAKE,
    MAINTENANCE,
    MODULARIZE,
    evaluar_restricciones_sostenibilidad,
)

BASE = {
    "B": 12,
    "T": 2,
    "dSdt": 3,
    "G": 0.7,
    "N": 4,
    "N_star": 5,
    "exposicion": 0.4,
    "E_max": 0.8,
    "resiliencia": 0.9,
    "R_min": 0.6,
}


def test_all_constraints_pass_but_financial_execution_stays_disabled() -> None:
    result = evaluar_restricciones_sostenibilidad(**BASE)

    assert result["estado"] == CONTINUE
    assert result["fallos"] == []
    assert result["crecimiento_permitido"] is True
    assert result["ejecucion_financiera_autorizada"] is False


@pytest.mark.parametrize(
    ("overrides", "expected_state", "expected_failure"),
    [
        ({"B": 5}, MAINTENANCE, MAINTENANCE),
        ({"G": 1.0}, DYNAMIC_BRAKE, DYNAMIC_BRAKE),
        ({"N": 6}, MODULARIZE, MODULARIZE),
        ({"exposicion": 0.81}, MODULARIZE, MODULARIZE),
        ({"resiliencia": 0.59}, MODULARIZE, MODULARIZE),
    ],
)
def test_each_hard_constraint_blocks_growth(
    overrides: dict, expected_state: str, expected_failure: str
) -> None:
    inputs = {**BASE, **overrides}
    result = evaluar_restricciones_sostenibilidad(**inputs)

    assert result["estado"] == expected_state
    assert expected_failure in result["fallos"]
    assert result["crecimiento_permitido"] is False
    assert result["ejecucion_financiera_autorizada"] is False


def test_simultaneous_failures_are_all_reported_and_maintenance_has_priority() -> None:
    result = evaluar_restricciones_sostenibilidad(
        **{**BASE, "B": 1, "G": 1.2, "N": 8, "exposicion": 2.0}
    )

    assert result["estado"] == MAINTENANCE
    assert result["fallos"] == [MAINTENANCE, DYNAMIC_BRAKE, MODULARIZE]
    assert result["crecimiento_permitido"] is False


def test_two_early_warnings_trigger_dynamic_brake() -> None:
    result = evaluar_restricciones_sostenibilidad(
        **BASE, varianza_creciente=True, recuperacion_lenta=True
    )

    assert result["estado"] == DYNAMIC_BRAKE
    assert result["fallos"] == [DYNAMIC_BRAKE]
    assert result["alertas"] == ["VARIANZA_CRECENTE", "RECUPERACION_LENTA"]


def test_single_early_warning_is_reported_without_hard_brake() -> None:
    result = evaluar_restricciones_sostenibilidad(**BASE, varianza_creciente=True)

    assert result["estado"] == CONTINUE
    assert result["alertas"] == ["VARIANZA_CRECENTE"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("B", float("nan")),
        ("G", float("inf")),
        ("T", True),
        ("dSdt", -1),
        ("N", 2.5),
    ],
)
def test_invalid_numeric_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        evaluar_restricciones_sostenibilidad(**{**BASE, field: value})


def test_non_boolean_early_warning_flag_is_rejected() -> None:
    with pytest.raises(ValueError, match="varianza_creciente"):
        evaluar_restricciones_sostenibilidad(**BASE, varianza_creciente=1)


def test_fex_key_rotation_keeps_overlap_key_valid_until_retirement(monkeypatch):
    import json

    from FEX.GOVERNANCE.sustainability import (
        FEX_ACTIVE_KEY_ID_ENV,
        FEX_KEYRING_ENV,
        verificar_integridad_evidencia,
    )

    old_key = "synthetic-old-fex-key-material-32-bytes"
    new_key = "synthetic-new-fex-key-material-32-bytes"
    monkeypatch.setenv(FEX_KEYRING_ENV, json.dumps({"fex-v1": old_key, "fex-v2": new_key}))
    monkeypatch.setenv(FEX_ACTIVE_KEY_ID_ENV, "fex-v1")
    report = evaluar_restricciones_sostenibilidad(**BASE)
    assert report["evidence_key_id"] == "fex-v1"
    assert verificar_integridad_evidencia(report) is True

    # Switching the active signing key does not invalidate evidence signed by
    # the old key while the old key remains in the verification overlap set.
    monkeypatch.setenv(FEX_ACTIVE_KEY_ID_ENV, "fex-v2")
    assert verificar_integridad_evidencia(report) is True

    # Retirement is explicit: once the old key leaves the keyring, its evidence
    # fails closed and requires controlled regeneration/reconciliation.
    monkeypatch.setenv(FEX_KEYRING_ENV, json.dumps({"fex-v2": new_key}))
    assert verificar_integridad_evidencia(report) is False


def test_fex_keyring_invalid_configuration_fails_closed(monkeypatch):
    import json

    from FEX.GOVERNANCE.sustainability import (
        FEX_ACTIVE_KEY_ID_ENV,
        FEX_KEYRING_ENV,
        verificar_integridad_evidencia,
    )

    monkeypatch.setenv(FEX_KEYRING_ENV, json.dumps({"fex-v1": "too-short"}))
    monkeypatch.setenv(FEX_ACTIVE_KEY_ID_ENV, "fex-v1")
    report = evaluar_restricciones_sostenibilidad(**BASE)
    assert report["evidence_signature"] is None
    assert verificar_integridad_evidencia(report) is False


def test_fex_legacy_evidence_remains_verifiable_during_key_overlap(monkeypatch):
    import hashlib
    import hmac
    import json

    from FEX.GOVERNANCE.sustainability import (
        FEX_ACTIVE_KEY_ID_ENV,
        FEX_KEYRING_ENV,
        hash_evidencia_sostenibilidad,
        verificar_integridad_evidencia,
    )

    old_key = "synthetic-legacy-fex-key-material-32-bytes"
    new_key = "synthetic-next-fex-key-material-32-bytes"
    monkeypatch.setenv(FEX_KEYRING_ENV, json.dumps({"legacy": old_key, "fex-v2": new_key}))
    monkeypatch.setenv(FEX_ACTIVE_KEY_ID_ENV, "fex-v2")

    # Simulate a report signed by the pre-keyring implementation, which did not
    # include evidence_key_id in its signed payload.
    report = evaluar_restricciones_sostenibilidad(**BASE)
    report.pop("evidence_key_id", None)
    report["evidence_hash"] = hash_evidencia_sostenibilidad(report)
    canonical = json.dumps(
        {"evidence_hash": report["evidence_hash"]},
        sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    report["evidence_signature"] = hmac.new(old_key.encode(), canonical, hashlib.sha256).hexdigest()
    assert verificar_integridad_evidencia(report) is True

    # Removing the legacy key ends the migration overlap; old evidence fails closed.
    monkeypatch.setenv(FEX_KEYRING_ENV, json.dumps({"fex-v2": new_key}))
    assert verificar_integridad_evidencia(report) is False
