"""Fail-closed order authorization tests; all writes are isolated under tmp_path."""
from __future__ import annotations

import os

import json

import pytest

from AEX.DECISION import operador, ordenes
from DSX.DEFENSE import defense
from DSX.DEFENSE.guards import final_execution_guard, verificar_autorizacion_ejecucion
from FEX.GOVERNANCE.sustainability import evaluar_restricciones_sostenibilidad


os.environ.setdefault("CATEDRALX_FEX_EVIDENCE_SECRET", "test-only-fex-evidence-secret-32-bytes")


def valid_decision():
    return {"accion": "ENTRAR_LARGO", "tamano": 0.1, "confianza": 0.8, "razon": "synthetic safety test"}


def setup_safe_paths(tmp_path, monkeypatch):
    output = tmp_path / "orden.json"
    panic_dir = tmp_path / "defense"
    panic_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(ordenes, "COMMAND_OUTPUT", output)
    monkeypatch.setattr(defense, "PATH_PANIC", panic_dir / ".panic")
    monkeypatch.setattr(ordenes, "APPROVAL_DIR", tmp_path / "approvals")
    monkeypatch.setenv("CATEDRALX_APPROVAL_SECRET", "test-only-secret-material-32-bytes-min")
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_SECRET", "test-only-dsx-secret-material-32-bytes")

    def test_only_identity_provider(assertion, decision, price):
        if not isinstance(assertion, dict) or assertion.get("test_issuer") != "trusted-test-idp":
            return {"verified": False}
        if assertion.get("action") != decision.get("accion") or assertion.get("price") != price:
            return {"verified": False}
        return {"verified": assertion.get("verified") is True,
                "subject": assertion.get("subject", ""),
                "permissions": assertion.get("permissions", [])}

    monkeypatch.setattr(ordenes, "APPROVER_IDENTITY_VERIFIER", test_only_identity_provider)
    return output


def signed_token(decision=None, price=100.0, **kwargs):
    decision = decision or valid_decision()
    assertion = {"test_issuer": "trusted-test-idp", "verified": True,
                 "subject": "synthetic-test-approver",
                 "permissions": ["financial_order_approve"],
                 "action": decision.get("accion"), "price": price}
    return ordenes.crear_token_aprobacion(decision, price, identity_assertion=assertion, **kwargs)


def test_approval_fails_closed_without_external_identity_provider(monkeypatch):
    monkeypatch.setenv("CATEDRALX_APPROVAL_SECRET", "test-only-secret-material-32-bytes-min")
    monkeypatch.setattr(ordenes, "APPROVER_IDENTITY_VERIFIER", None)
    with pytest.raises(PermissionError, match="verificador externo"):
        ordenes.crear_token_aprobacion(valid_decision(), 100.0,
                                       identity_assertion={"subject": "claimed-admin"})


def test_approval_rejects_forged_identity_assertion(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    with pytest.raises(PermissionError, match="no verificada"):
        ordenes.crear_token_aprobacion(valid_decision(), 100.0,
            identity_assertion={"subject": "admin", "verified": True,
                                "permissions": ["financial_order_approve"]})


def test_approval_rejects_identity_without_required_permission(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    assertion = {"test_issuer": "trusted-test-idp", "verified": True,
                 "subject": "synthetic-viewer", "permissions": ["read_only"],
                 "action": "ENTRAR_LARGO", "price": 100.0}
    with pytest.raises(PermissionError, match="permiso requerido"):
        ordenes.crear_token_aprobacion(valid_decision(), 100.0, identity_assertion=assertion)


def test_approval_rejects_identity_assertion_bound_to_different_action_or_price(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    assertion = {"test_issuer": "trusted-test-idp", "verified": True,
                 "subject": "synthetic-test-approver",
                 "permissions": ["financial_order_approve"],
                 "action": "ENTRAR_CORTO", "price": 100.0}
    with pytest.raises(PermissionError, match="no verificada"):
        ordenes.crear_token_aprobacion(valid_decision(), 100.0, identity_assertion=assertion)


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


def test_order_creation_requires_signed_token_not_boolean(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    with pytest.raises(PermissionError, match="token_aprobacion"):
        ordenes.generar_orden(valid_decision(), 100.0, autorizacion_explicita=True)
    assert not output.exists()
    assert not output.with_name("decisiones.jsonl").exists()


def test_signed_token_alone_cannot_create_order_without_dsx_governance_gate(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    with pytest.raises(PermissionError, match="DSX"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion=signed_token())
    assert not output.exists()
    assert not output.with_name("decisiones.jsonl").exists()


def test_order_creation_rejects_dsx_gate_without_verified_governance(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    incomplete_gate = {"enforcement_vector": "DSX", "allowed": True, "blocked": False,
                      "financial_execution_authorized": False}
    with pytest.raises(PermissionError, match="gobernanza ausente"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion=signed_token(),
                              dsx_authorization=incomplete_gate)
    assert not output.exists()


def test_order_creation_fails_closed_if_panic_directory_is_unavailable(tmp_path, monkeypatch):
    output = tmp_path / "orden.json"
    monkeypatch.setattr(ordenes, "COMMAND_OUTPUT", output)
    monkeypatch.setattr(defense, "PATH_PANIC", tmp_path / "missing" / ".panic")
    monkeypatch.setenv("CATEDRALX_APPROVAL_SECRET", "test-only-secret-material-32-bytes-min")
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_SECRET", "test-only-dsx-secret-material-32-bytes")
    monkeypatch.setattr(ordenes, "APPROVER_IDENTITY_VERIFIER",
        lambda assertion, decision, price: {"verified": True, "subject": "synthetic-test-approver",
                                            "permissions": ["financial_order_approve"]})
    with pytest.raises(PermissionError, match="Ubicación del bloqueo"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion=signed_token())
    assert not output.exists()


def test_order_creation_is_blocked_by_panic_marker(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    defense.PATH_PANIC.write_text("synthetic test lock", encoding="utf-8")
    with pytest.raises(PermissionError, match="emergencia"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion=signed_token())
    assert not output.exists()


@pytest.mark.parametrize(("price", "size", "confidence"), [
    (float("nan"), 0.1, 0.8), (float("inf"), 0.1, 0.8),
    (100.0, float("nan"), 0.8), (100.0, float("inf"), 0.8),
    (100.0, 0.1, float("nan")), (100.0, 0.1, float("inf")),
    (100.0, 0.1, 1.01), (100.0, 0.0, 0.8),
])
def test_order_creation_rejects_nonfinite_or_out_of_range_values(tmp_path, monkeypatch, price, size, confidence):
    setup_safe_paths(tmp_path, monkeypatch)
    decision = {**valid_decision(), "tamano": size, "confianza": confidence}
    with pytest.raises((ValueError, PermissionError)):
        ordenes.generar_orden(decision, price, token_aprobacion=signed_token(decision, price if price == price and abs(price) != float('inf') else 100.0))


def test_dsx_gate_dictionary_cannot_be_forged_without_signature(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    forged = {"enforcement_vector": "DSX", "allowed": True, "blocked": False,
              "governance_status": "verified", "governance_metrics_complete": True,
              "financial_execution_authorized": False}
    with pytest.raises(PermissionError, match="autorización firmada"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion=signed_token(),
                              dsx_authorization=forged)


def test_dsx_signature_is_bound_to_exact_decision_and_price(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    decision = valid_decision()
    authorization = valid_dsx_authorization()
    changed = {**decision, "tamano": 0.2}
    with pytest.raises(PermissionError, match="no corresponde"):
        ordenes.generar_orden(changed, 100.0,
                              token_aprobacion=signed_token(changed, 100.0),
                              dsx_authorization=authorization)
    with pytest.raises(PermissionError, match="no corresponde"):
        ordenes.generar_orden(decision, 101.0,
                              token_aprobacion=signed_token(decision, 101.0),
                              dsx_authorization=authorization)


def test_authorized_order_is_pending_and_token_is_one_time(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    decision = valid_decision()
    token = signed_token(decision, 100.0)
    result = ordenes.generar_orden(decision, 100.0, token_aprobacion=token,
                                    dsx_authorization=valid_dsx_authorization())
    assert result["estado"] == "PENDIENTE"
    assert result["autorizacion_verificada"] is True
    assert result["aprobador"] == "synthetic-test-approver"
    assert json.loads(output.read_text(encoding="utf-8")) == result
    repeated = ordenes.generar_orden(decision, 100.0, token_aprobacion=token,
                                      dsx_authorization=valid_dsx_authorization())
    assert repeated["id"] == result["id"]
    assert repeated["approval_token_hash"] == result["approval_token_hash"]


def test_order_retry_recovers_after_crash_between_token_consumption_and_order_write(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    decision = valid_decision()
    token = signed_token(decision, 100.0)
    original_write = ordenes._escribir_atomico
    monkeypatch.setattr(
        ordenes, "_escribir_atomico",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("synthetic crash before order write")),
    )
    with pytest.raises(OSError, match="synthetic crash before order write"):
        ordenes.generar_orden(
            decision, 100.0, token_aprobacion=token,
            dsx_authorization=valid_dsx_authorization(),
        )
    assert not output.exists()
    assert list((tmp_path / "approvals").glob("*.used"))
    monkeypatch.setattr(ordenes, "_escribir_atomico", original_write)
    recovered = ordenes.generar_orden(
        decision, 100.0, token_aprobacion=token,
        dsx_authorization=valid_dsx_authorization(),
    )
    assert recovered["approval_token_hash"] == ordenes._hash_token_aprobacion(token)
    assert json.loads(output.read_text(encoding="utf-8"))["id"] == recovered["id"]


def test_order_retry_recovers_after_history_write_failure(tmp_path, monkeypatch):
    output = setup_safe_paths(tmp_path, monkeypatch)
    decision = valid_decision()
    token = signed_token(decision, 100.0)
    original_guardar_memoria = ordenes._guardar_memoria
    monkeypatch.setattr(ordenes, "_guardar_memoria",
                        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("synthetic history failure")))
    with pytest.raises(OSError, match="synthetic history failure"):
        ordenes.generar_orden(decision, 100.0, token_aprobacion=token,
                              dsx_authorization=valid_dsx_authorization())
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["approval_token_hash"] == ordenes._hash_token_aprobacion(token)
    monkeypatch.setattr(ordenes, "_guardar_memoria", original_guardar_memoria)
    assert ordenes.recuperar_memoria_desde_orden() is True
    history = output.with_name("decisiones.jsonl").read_text(encoding="utf-8")
    assert ordenes._hash_token_aprobacion(token) in history
    repeated = ordenes.generar_orden(decision, 100.0, token_aprobacion=token,
                                     dsx_authorization=valid_dsx_authorization())
    assert repeated["id"] == persisted["id"]


def test_token_cannot_authorize_modified_order(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    token = signed_token()
    modified = {**valid_decision(), "tamano": 0.2}
    with pytest.raises(PermissionError, match="autorización firmada"):
        ordenes.generar_orden(modified, 100.0, token_aprobacion=token,
                               dsx_authorization=valid_dsx_authorization())


def test_expired_token_is_rejected(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    token = signed_token(emitido_en=1)
    with pytest.raises(PermissionError, match="caducada"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion=token,
                               dsx_authorization=valid_dsx_authorization())


def test_bad_secret_fails_closed(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("CATEDRALX_APPROVAL_SECRET", "too-short")
    with pytest.raises(PermissionError, match="Token de autorización inválido"):
        ordenes.generar_orden(valid_decision(), 100.0, token_aprobacion="{}",
                               dsx_authorization=valid_dsx_authorization())


def test_operator_filters_never_claim_explicit_execution_authorization():
    result = operador.ensamblar_operacion(score_direccional=0.68, confianza=0.85, fase="TENDENCIA",
        size_kelly=0.15, size_kelly_adapted=0.12, size_mcx=0.10, size_dsx=0.08, size_fe=0.05, size_expo=0.20)
    assert result["ejecucion_autorizada"] is False
    assert result["requiere_autorizacion_explicita"] is True



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


def test_approval_key_rotation_accepts_overlap_key_and_rejects_removed_key(tmp_path, monkeypatch):
    old_key = "old-approval-test-key-material-at-least-32-bytes"
    new_key = "new-approval-test-key-material-at-least-32-bytes"
    setup_safe_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"v1": old_key, "v2": new_key}))
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "v1")
    decision = valid_decision()
    token = signed_token(decision, 100.0)
    token_again = signed_token(decision, 100.0)
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "v2")
    assert ordenes._consumir_token_aprobacion(token, decision, 100.0) == "synthetic-test-approver"
    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"v2": new_key}))
    with pytest.raises(PermissionError, match="Clave de aprobación desconocida"):
        ordenes._consumir_token_aprobacion(token_again, decision, 100.0)


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


def test_approval_key_rotation_accepts_overlap_key_and_rejects_retired_key(tmp_path, monkeypatch):
    import json

    setup_safe_paths(tmp_path, monkeypatch)
    old_key = "synthetic-approval-old-key-material-32"
    new_key = "synthetic-approval-new-key-material-32"
    monkeypatch.delenv("CATEDRALX_APPROVAL_SECRET", raising=False)
    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"old": old_key, "new": new_key}))
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "old")
    decision = valid_decision()
    token = signed_token(decision, 100.0)

    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "new")
    assert ordenes._consumir_token_aprobacion(token, decision, 100.0) == "synthetic-test-approver"

    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"new": new_key}))
    with pytest.raises(PermissionError, match="Clave de aprobación desconocida"):
        ordenes._consumir_token_aprobacion(token, decision, 100.0)


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

    monkeypatch.delenv("CATEDRALX_APPROVAL_SECRET", raising=False)
    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"old": "synthetic-approval-key-material-32"}))
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "missing")
    with pytest.raises(PermissionError, match="clave activa válida"):
        ordenes._approval_keyring()


def test_versioned_dsx_and_fex_key_rotation_keeps_overlap_then_rejects_retired_keys(monkeypatch):
    import json
    from DSX.DEFENSE.guards import verificar_autorizacion_ejecucion

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


def test_concurrent_retries_with_same_approval_never_persist_duplicate_orders(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    output = setup_safe_paths(tmp_path, monkeypatch)
    decision = valid_decision()
    token = signed_token(decision, 100.0)
    authorization = valid_dsx_authorization()

    def attempt():
        try:
            return ordenes.generar_orden(
                decision, 100.0, token_aprobacion=token,
                dsx_authorization=authorization,
            )
        except PermissionError:
            # A competing worker may observe the one-time marker before the
            # winning worker has atomically published the canonical order.
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _index: attempt(), range(8)))

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["approval_token_hash"] == ordenes._hash_token_aprobacion(token)
    successful_ids = {item["id"] for item in results if isinstance(item, dict)}
    assert successful_ids <= {persisted["id"]}
    history_path = output.with_name("decisiones.jsonl")
    if history_path.exists():
        history = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()]
        matching = [row for row in history if row.get("approval_token_hash") == persisted["approval_token_hash"]]
        assert len(matching) <= 1


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


def test_approval_key_rotation_keeps_overlap_token_verifiable(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    old_secret = "old-approval-rotation-secret-material-32"
    new_secret = "new-approval-rotation-secret-material-32"
    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"old": old_secret, "new": new_secret}))
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "new")
    token = signed_token()
    assert json.loads(token)["payload"]["key_id"] == "new"

    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "old")
    assert ordenes._consumir_token_aprobacion(token, valid_decision(), 100.0) == "synthetic-test-approver"


def test_versioned_keyrings_keep_overlap_keys_verifiable_during_rotation(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    old_key = "synthetic-old-rotation-key-material-0001"
    new_key = "synthetic-new-rotation-key-material-0002"

    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"dsx-v1": old_key, "dsx-v2": new_key}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v2")
    monkeypatch.setenv("CATEDRALX_FEX_KEYRING", json.dumps({"fex-v1": old_key, "fex-v2": new_key}))
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "fex-v2")
    monkeypatch.setenv("CATEDRALX_APPROVAL_KEYRING", json.dumps({"approval-v1": old_key, "approval-v2": new_key}))
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "approval-v2")

    decision = valid_decision()
    approval_token = signed_token(decision, 100.0)
    dsx_authorization = valid_dsx_authorization()
    assert json.loads(approval_token)["payload"]["key_id"] == "approval-v2"
    assert dsx_authorization["dsx_signed_payload"]["key_id"] == "dsx-v2"

    # Simulate promotion/rollback of the active key while retaining overlap keys.
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v1")
    monkeypatch.setenv("CATEDRALX_FEX_ACTIVE_KEY_ID", "fex-v1")
    monkeypatch.setenv("CATEDRALX_APPROVAL_ACTIVE_KEY_ID", "approval-v1")
    assert ordenes._consumir_token_aprobacion(approval_token, decision, 100.0) == "synthetic-test-approver"
    from DSX.DEFENSE.guards import verificar_autorizacion_ejecucion
    assert verificar_autorizacion_ejecucion(dsx_authorization, decision, 100.0) is True
    report = dsx_authorization["sustainability_gate"] if "sustainability_gate" in dsx_authorization else None
    assert report is None or report["financial_execution_authorized"] is False


def test_versioned_keyrings_fail_closed_for_unknown_key_ids(tmp_path, monkeypatch):
    setup_safe_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_KEYRING", json.dumps({"dsx-v2": "synthetic-new-rotation-key-material-0002"}))
    monkeypatch.setenv("CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID", "dsx-v2")
    forged = {"dsx_signed_payload": {"key_id": "dsx-retired", "issued_at": 1},
              "dsx_signature": "not-a-signature"}
    from DSX.DEFENSE.guards import verificar_autorizacion_ejecucion
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
