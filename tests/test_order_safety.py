"""Fail-closed authorization tests; all writes are isolated under tmp_path.

H-01 (misión LIBERACIÓN): the order-authoring API (``generar_orden``,
``crear_token_aprobacion``, ``orden.json``) was REMOVED from
``AEX/DECISION/ordenes.py``. The tests that exercised it were removed with
it in the same change. What remains here:

- the removal itself, asserted structurally (no order API must exist);
- the Ed25519 approver-identity verifier that ``economic_cycle.py`` still
  uses for economic-cycle authorization;
- the DSX/FEX key-rotation and operator tests, which never depended on
  order authoring.
"""
from __future__ import annotations

import json
import os

import pytest
from AEX.DECISION import operador, ordenes
from DSX.DEFENSE.guards import final_execution_guard, verificar_autorizacion_ejecucion
from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad

os.environ.setdefault("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")


def valid_decision():
    return {"accion": "ENTRAR_LARGO", "tamano": 0.1, "confianza": 0.8, "razon": "synthetic safety test"}


def valid_dsx_authorization():
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    return final_execution_guard(
        {"disonancia": 0.1, "evidence_status": "computed"},
        {"fuerza_contra": 0.1, "evidence_status": "computed"},
        report, decision_context=valid_decision(), reference_price=100.0,
    )


# --- H-01: order authoring must not exist anymore ---------------------------

_REMOVED_ORDER_API = (
    "generar_orden",
    "_generar_orden_bajo_bloqueo",
    "crear_token_aprobacion",
    "_consumir_token_aprobacion",
    "_cargar_orden_idempotente",
    "_escribir_atomico",
    "recuperar_memoria_desde_orden",
    "_guardar_memoria",
    "verificar_identidad_aprobador",
    "_approval_keyring",
    "_approval_key",
    "_registrar_nonce_ed25519",
    "_nonce_usado_ed25519",
    "COMMAND_OUTPUT",
    "APPROVAL_DIR",
    "STOP_LOSS_PCT",
    "TAKE_PROFIT_PCT",
)


def test_order_authoring_api_was_removed():
    for name in _REMOVED_ORDER_API:
        assert not hasattr(ordenes, name), f"ordenes.{name} must not exist (H-01)"


def test_no_order_module_state_can_persist_an_order(tmp_path, monkeypatch):
    # There is no output path, no approval directory and no token machinery
    # left for any caller to aim at.
    assert not hasattr(ordenes, "COMMAND_OUTPUT")
    assert not hasattr(ordenes, "APPROVAL_DIR")
    assert "orden" not in {name.lower() for name in dir(ordenes) if "orden" in name.lower()}


def test_approver_identity_verifier_survives_for_economic_cycles():
    # economic_cycle.py authorizes economic cycles through this verifier;
    # that approved use is why the module itself was kept (H-01).
    assert ordenes.APPROVER_IDENTITY_VERIFIER is ordenes._ed25519_approver_verifier
    from FEX.GOVERNANCE import economic_cycle

    assert economic_cycle is not None


def test_approver_identity_verifier_fails_closed_without_public_key(monkeypatch):
    import time

    now = int(time.time())
    monkeypatch.delenv("CHALAMANDRA_APPROVER_PUBLIC_KEY", raising=False)
    with pytest.raises(PermissionError, match="no configurada"):
        ordenes.APPROVER_IDENTITY_VERIFIER(
            {"subject": "x", "permissions": ["economic_cycle_authorize"],
             "purpose": "catedralx_economic_cycle_authorization",
             "iat": now, "exp": now + 60, "nonce": "n", "signature": "00" * 32},
            {"purpose": "catedralx_economic_cycle_authorization"},
            0.0,
        )


def test_operator_filters_never_claim_explicit_execution_authorization():
    result = operador.ensamblar_operacion(score_direccional=0.68, confianza=0.85, fase="TENDENCIA",
        size_kelly=0.15, size_kelly_adapted=0.12, size_mcx=0.10, size_dsx=0.08, size_fe=0.05, size_expo=0.20)
    assert result["ejecucion_autorizada"] is False
    assert result["requiere_autorizacion_explicita"] is True


# --- DSX / FEX key rotation (unchanged: never depended on orders) -----------

def test_dsx_authorization_expires_after_ttl(monkeypatch):
    from DSX.DEFENSE import guards

    monkeypatch.setenv("CATEDRALX_DSX_AUTH_SECRET", "test-only-dsx-secret-material-32-bytes")
    monkeypatch.setenv("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")
    decision = valid_decision()
    authorization = valid_dsx_authorization()
    issued = authorization["dsx_signed_payload"]["issued_at"]
    monkeypatch.setattr(guards.time, "time", lambda: issued + guards.DSX_AUTH_TTL_SECONDS + 1)
    assert guards.verificar_autorizacion_ejecucion(authorization, decision, 100.0) is False


def test_dsx_key_rotation_accepts_overlap_key_and_rejects_removed_key(monkeypatch):
    from DSX.DEFENSE import guards

    old_key = "old-dsx-test-key-material-at-least-32-bytes"
    new_key = "new-dsx-test-key-material-at-least-32-bytes"
    monkeypatch.setenv("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"v1": old_key, "v2": new_key}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "v1")
    authorization = valid_dsx_authorization()
    assert guards.verificar_autorizacion_ejecucion(authorization, valid_decision(), 100.0)
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "v2")
    assert guards.verificar_autorizacion_ejecucion(authorization, valid_decision(), 100.0)
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"v2": new_key}))
    assert not guards.verificar_autorizacion_ejecucion(authorization, valid_decision(), 100.0)


def test_fex_key_rotation_accepts_overlap_key_and_rejects_removed_key(monkeypatch):
    from FEX.GOVERNANCE import sustainability

    old_key = "old-fex-test-key-material-at-least-32-bytes"
    new_key = "new-fex-test-key-material-at-least-32-bytes"
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"v1": old_key, "v2": new_key}))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "v1")
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    assert sustainability.verificar_integridad_evidencia(report)
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "v2")
    assert sustainability.verificar_integridad_evidencia(report)
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"v2": new_key}))
    assert not sustainability.verificar_integridad_evidencia(report)


def test_dsx_key_rotation_accepts_overlap_key_and_rejects_retired_key(monkeypatch):
    import json

    from DSX.DEFENSE import guards

    old_key = "synthetic-dsx-old-key-material-32-bytes"
    new_key = "synthetic-dsx-new-key-material-32-bytes"
    monkeypatch.delenv("CATEDRALX_DSX_AUTH_SECRET", raising=False)
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"old": old_key, "new": new_key}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "old")
    decision = valid_decision()
    authorization = valid_dsx_authorization()
    assert authorization["dsx_signed_payload"]["key_id"] == "old"

    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "new")
    assert guards.verificar_autorizacion_ejecucion(authorization, decision, 100.0)

    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"new": new_key}))
    assert not guards.verificar_autorizacion_ejecucion(authorization, decision, 100.0)


def test_fex_key_rotation_accepts_overlap_key_and_rejects_retired_key(monkeypatch):
    import json

    from FEX.GOVERNANCE import sustainability

    old_key = "synthetic-fex-old-key-material-32-bytes"
    new_key = "synthetic-fex-new-key-material-32-bytes"
    monkeypatch.delenv("CATEDRALX_FEX_EVIDENCE_SECRET", raising=False)
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"old": old_key, "new": new_key}))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "old")
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    assert report["evidence_key_id"] == "old"
    assert sustainability.verificar_integridad_evidencia(report)

    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "new")
    assert sustainability.verificar_integridad_evidencia(report)

    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"new": new_key}))
    assert not sustainability.verificar_integridad_evidencia(report)


def test_versioned_keyrings_fail_closed_on_missing_active_key(monkeypatch):
    import json

    from DSX.DEFENSE import guards
    from FEX.GOVERNANCE import sustainability

    monkeypatch.delenv("CATEDRALX_DSX_AUTH_SECRET", raising=False)
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"old": "synthetic-dsx-key-material-32-bytes"}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "missing")
    with pytest.raises(PermissionError, match="clave activa válida"):
        guards._dsx_auth_keyring()

    monkeypatch.delenv("CATEDRALX_FEX_EVIDENCE_SECRET", raising=False)
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"old": "synthetic-fex-key-material-32-bytes"}))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "missing")
    with pytest.raises(PermissionError, match="clave activa válida"):
        sustainability._fex_evidence_keyring()


def test_versioned_dsx_and_fex_key_rotation_keeps_overlap_then_rejects_retired_keys(monkeypatch):
    import json

    old_dsx = "old-dsx-test-secret-material-32-bytes"
    new_dsx = "new-dsx-test-secret-material-32-bytes"
    old_fex = "old-fex-test-secret-material-32-bytes"
    new_fex = "new-fex-test-secret-material-32-bytes"
    dsx_ring = {"dsx-v1": old_dsx, "dsx-v2": new_dsx}
    fex_ring = {"fex-v1": old_fex, "fex-v2": new_fex}
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps(dsx_ring))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v1")
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps(fex_ring))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "fex-v1")

    decision = valid_decision()
    authorization = valid_dsx_authorization()

    # Rotate active signing keys while retaining the previous keys for verification.
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v2")
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "fex-v2")
    assert verificar_autorizacion_ejecucion(authorization, decision, 100.0) is True

    # Once old keys are removed, artifacts signed with them must be rejected.
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"dsx-v2": new_dsx}))
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"fex-v2": new_fex}))
    assert verificar_autorizacion_ejecucion(authorization, decision, 100.0) is False


def test_dsx_key_rotation_keeps_overlap_key_verifiable(monkeypatch):
    from DSX.DEFENSE import guards

    old_secret = "old-dsx-rotation-secret-material-32-bytes"
    new_secret = "new-dsx-rotation-secret-material-32-bytes"
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"old": old_secret, "new": new_secret}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "new")
    authorization = valid_dsx_authorization()
    assert authorization["dsx_signed_payload"]["key_id"] == "new"
    assert guards.verificar_autorizacion_ejecucion(authorization, valid_decision(), 100.0)

    # Promote the old key only after overlap; tokens signed by new remain verifiable.
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "old")
    assert guards.verificar_autorizacion_ejecucion(authorization, valid_decision(), 100.0)

    # Once the new key is retired, a token explicitly signed by it must fail closed.
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"old": old_secret}))
    assert not guards.verificar_autorizacion_ejecucion(authorization, valid_decision(), 100.0)


def test_fex_key_rotation_keeps_overlap_evidence_verifiable(monkeypatch):
    from FEX.GOVERNANCE import sustainability

    old_secret = "old-fex-rotation-secret-material-32-bytes"
    new_secret = "new-fex-rotation-secret-material-32-bytes"
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"old": old_secret, "new": new_secret}))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "new")
    report = evaluar_restricciones_sostenibilidad(
        B=12, T=2, dSdt=3, G=0.7, N=4, N_star=5,
        exposicion=0.4, E_max=0.8, resiliencia=0.9, R_min=0.6,
    )
    assert report["evidence_key_id"] == "new"
    assert sustainability.verificar_integridad_evidencia(report)

    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "old")
    assert sustainability.verificar_integridad_evidencia(report)

    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"old": old_secret}))
    assert not sustainability.verificar_integridad_evidencia(report)


def test_versioned_keyrings_keep_overlap_keys_verifiable_during_rotation(monkeypatch):
    old_key = "synthetic-old-rotation-key-material-0001"
    new_key = "synthetic-new-rotation-key-material-0002"

    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"dsx-v1": old_key, "dsx-v2": new_key}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v2")
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"fex-v1": old_key, "fex-v2": new_key}))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "fex-v2")

    decision = valid_decision()
    dsx_authorization = valid_dsx_authorization()
    assert dsx_authorization["dsx_signed_payload"]["key_id"] == "dsx-v2"

    # Simulate promotion/rollback of the active key while retaining overlap keys.
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v1")
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "fex-v1")
    assert verificar_autorizacion_ejecucion(dsx_authorization, decision, 100.0) is True
    report = dsx_authorization["sustainability_gate"] if "sustainability_gate" in dsx_authorization else None
    assert report is None or report["financial_execution_authorized"] is False


def test_versioned_keyrings_fail_closed_for_unknown_key_ids(monkeypatch):
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"dsx-v2": "synthetic-new-rotation-key-material-0002"}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v2")
    forged = {"dsx_signed_payload": {"key_id": "dsx-retired", "issued_at": 1},
              "dsx_signature": "not-a-signature"}
    assert verificar_autorizacion_ejecucion(forged, valid_decision(), 100.0) is False


def test_dsx_key_rotation_keeps_overlap_key_valid_until_retirement(monkeypatch):
    import json

    from DSX.DEFENSE import guards

    old_key = "synthetic-old-dsx-key-material-32-bytes"
    new_key = "synthetic-new-dsx-key-material-32-bytes"
    monkeypatch.setenv(guards.DSX_AUTH_KEYRING_ENV,
                       json.dumps({"dsx-v1": old_key, "dsx-v2": new_key}))
    monkeypatch.setenv(guards.DSX_AUTH_ACTIVE_KEY_ID_ENV, "dsx-v1")
    monkeypatch.setenv("CATEDRALX_FEX_EVIDENCE_SECRET",
                       "test-only-fex-evidence-secret-32-bytes")
    monkeypatch.delenv("CATEDRALX_FEX_KEYRING", raising=False)
    monkeypatch.delenv("CATEDRALX_FEX_ACTIVE_KEY_ID", raising=False)

    decision = valid_decision()
    authorization = valid_dsx_authorization()
    assert authorization["dsx_signed_payload"]["key_id"] == "dsx-v1"
    assert guards.verificar_autorizacion_ejecucion(authorization, decision, 100.0) is True

    # New signatures use v2; old signatures remain verifiable during overlap.
    monkeypatch.setenv(guards.DSX_AUTH_ACTIVE_KEY_ID_ENV, "dsx-v2")
    assert guards.verificar_autorizacion_ejecucion(authorization, decision, 100.0) is True

    # Removing v1 is explicit retirement and invalidates artifacts signed by v1.
    monkeypatch.setenv(guards.DSX_AUTH_KEYRING_ENV, json.dumps({"dsx-v2": new_key}))
    assert guards.verificar_autorizacion_ejecucion(authorization, decision, 100.0) is False


def test_dsx_keyring_missing_active_key_fails_closed(monkeypatch):
    import json

    from DSX.DEFENSE import guards

    monkeypatch.setenv(guards.DSX_AUTH_KEYRING_ENV, json.dumps({"dsx-v1": "synthetic-dsx-key-material-32-bytes"}))
    monkeypatch.setenv(guards.DSX_AUTH_ACTIVE_KEY_ID_ENV, "unknown-key-id")
    with pytest.raises(PermissionError, match="clave activa"):
        guards._dsx_auth_keyring()
