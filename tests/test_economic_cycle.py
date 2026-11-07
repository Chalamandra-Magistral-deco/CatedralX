"""Governance, auditability, and fail-closed tests for the impact cycle."""

from __future__ import annotations

import json
import subprocess
import time
import uuid
from pathlib import Path

import pytest
from AEX.DECISION import ordenes
from FEX.GOVERNANCE.economic_cycle import (
    cargar_propuesta_autorizada, registrar_evento, resumir_ciclos,
)


def measure(path):
    return registrar_evento(
        "measure",
        {
            "metric": "personas_atendidas",
            "source": "registro_servicio_v1",
            "period": "2026-Q3",
            "unit": "personas",
            "formula": "conteo_unico_de_personas",
            "value": 120,
            "target": 150,
            "uncertainty": 3,
            "observed_at": "2026-10-23T10:00:00Z",
        },
        path,
    )


def test_cycle_requires_ordered_explicit_approval_and_stays_non_operational(tmp_path):
    path = tmp_path / "impact.jsonl"
    cycle = measure(path)
    with pytest.raises(ValueError, match="se requiere evaluate"):
        registrar_evento(
            "propose",
            {
                "proposal": "Mejorar cobertura",
                "expected_outcome": "Más personas atendidas",
                "verification_plan": "Comparar conteo trimestral",
            },
            path,
            cycle_id=cycle,
        )

    registrar_evento(
        "evaluate",
        {"assessment": "Por debajo del objetivo", "evidence": "registro_servicio_v1"},
        path,
        cycle_id=cycle,
    )
    registrar_evento(
        "propose",
        {
            "proposal": "Piloto de ampliación",
            "expected_outcome": "Aumentar cobertura",
            "verification_plan": "Medir conteo y coste por persona",
        },
        path,
        cycle_id=cycle,
    )
    with pytest.raises(ValueError, match="approved=true"):
        registrar_evento(
            "authorize",
            {"approved": False, "approver": "comité", "rationale": "pendiente"},
            path,
            cycle_id=cycle,
        )
    # CX-02: authorize sin identidad debe bloquear, no pasar como humano
    with pytest.raises(PermissionError, match="falta asercion"):
        registrar_evento(
            "authorize",
            {
                "approved": True,
                "approver": "comité",
                "rationale": "Piloto acotado con revisión",
            },
            path,
            cycle_id=cycle,
        )
    # CX-02: con identidad verificada (mock) si pasa
    _orig = ordenes.APPROVER_IDENTITY_VERIFIER
    ordenes.APPROVER_IDENTITY_VERIFIER = lambda assertion, ctx, val: {"verified": True, "subject": "comité", "permissions": ["economic_cycle_authorize"]}
    try:
        registrar_evento(
            "authorize",
            {
                "approved": True,
                "approver": "comité",
                "rationale": "Piloto acotado con revisión",
                "identity_assertion": {"subject": "comité", "signature": "mock"},
            },
            path,
            cycle_id=cycle,
        )
    finally:
        ordenes.APPROVER_IDENTITY_VERIFIER = _orig
    registrar_evento(
        "verify",
        {
            "evidence": "informe de piloto",
            "result": "medición posterior registrada",
            "verified_at": "2026-11-01T00:00:00Z",
        },
        path,
        cycle_id=cycle,
    )
    registrar_evento(
        "feedback",
        {
            "lesson": "Medir coste por persona además del alcance",
            "next_action": "Revisar con nueva evidencia",
        },
        path,
        cycle_id=cycle,
    )

    report = resumir_ciclos(path)
    assert report["cycles_complete"] == 1
    assert report["automatic_reinvestment"] is False
    assert report["trading_enabled"] is False
    assert report["cycles"][0]["authorization_recorded"] is True
    assert report["cycles"][0]["identity_verified"] is False
    assert report["cycles"][0]["identity_verification_status"] == "not_reverified_read_only"
    assert report["cycles"][0]["human_authorized"] is False
    assert report["cycles"][0]["dispatch_eligible"] is False
    assert all(
        json.loads(line)["controls"]["money_moved"] is False
        for line in path.read_text().splitlines()
    )


def test_measure_requires_traceable_metric_and_timezone(tmp_path):
    with pytest.raises(ValueError, match="source"):
        registrar_evento(
            "measure",
            {
                "metric": "x",
                "period": "Q3",
                "unit": "n",
                "formula": "count",
                "value": 2,
                "observed_at": "2026-10-23T10:00:00Z",
            },
            tmp_path / "ledger.jsonl",
        )
    with pytest.raises(ValueError, match="zona horaria"):
        registrar_evento(
            "measure",
            {
                "metric": "x",
                "source": "db",
                "period": "Q3",
                "unit": "n",
                "formula": "count",
                "value": 2,
                "observed_at": "2026-10-23T10:00:00",
            },
            tmp_path / "ledger.jsonl",
        )


def test_no_arbitrary_allocation_percentages_or_unsupported_causal_claim(tmp_path):
    path = tmp_path / "impact.jsonl"
    cycle = measure(path)
    with pytest.raises(ValueError, match="causal_method"):
        registrar_evento(
            "evaluate",
            {
                "assessment": "Subió la métrica",
                "evidence": "dashboard",
                "causal_claim": True,
            },
            path,
            cycle_id=cycle,
        )
    registrar_evento(
        "evaluate",
        {
            "assessment": "Subió la métrica",
            "evidence": "dashboard; no prueba causalidad",
        },
        path,
        cycle_id=cycle,
    )
    with pytest.raises(ValueError, match="porcentajes"):
        registrar_evento(
            "propose",
            {
                "proposal": "Reinvertir",
                "expected_outcome": "Más capacidad",
                "verification_plan": "Medir",
                "allocation_pct": 20,
            },
            path,
            cycle_id=cycle,
        )


def test_malformed_ledger_fails_closed(tmp_path):
    path = tmp_path / "impact.jsonl"
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="línea 1"):
        resumir_ciclos(path)


def test_catedral_cli_exposes_governed_impact_report(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    ledger = tmp_path / "cli-impact.jsonl"
    completed = subprocess.run(
        [
            "bash",
            str(repo_root / "BIN/catedral"),
            "impact-cycle",
            "--report",
            "--path",
            str(ledger),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["read_only"] is True
    assert report["cycles_recorded"] == 0
    assert report["automatic_reinvestment"] is False
    assert report["trading_enabled"] is False


def test_ed25519_authorization_claims_nonce_once_and_reverifies_on_load(monkeypatch, tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    monkeypatch.setenv("CHALAMANDRA_APPROVER_PUBLIC_KEY", public_key.hex())
    monkeypatch.setenv("CATEDRALX_STATE_DIR", str(tmp_path / "state"))

    path = tmp_path / "impact.jsonl"
    cycle = measure(path)
    registrar_evento(
        "evaluate", {"assessment": "test", "evidence": "synthetic"},
        path, cycle_id=cycle,
    )
    proposal_payload = {
        "proposal": "review only",
        "expected_outcome": "candidate",
        "verification_plan": "compare next period",
    }
    registrar_evento("propose", proposal_payload, path, cycle_id=cycle)

    from FEX.GOVERNANCE import economic_cycle
    pre_authorization_events = [json.loads(line) for line in path.read_text().splitlines()]
    assertion = {
        "subject": "real-test-owner",
        "permissions": ["economic_cycle_authorize"],
        "purpose": "catedralx_economic_cycle_authorization",
        "cycle_id": cycle,
        "cycle_digest": economic_cycle._cycle_evidence_digest(pre_authorization_events),
        "iat": int(time.time()),
        "exp": int(time.time()) + 120,
        "nonce": str(uuid.uuid4()),
    }
    assertion["signature"] = private_key.sign(
        ordenes._canonical_json_ed25519(assertion)
    ).hex()

    registrar_evento(
        "authorize",
        {
            "approved": True,
            "approver": "real-test-owner",
            "rationale": "Ed25519 integration test",
            "identity_assertion": assertion,
        },
        path, cycle_id=cycle,
    )

    # Repeated read/dispatch validation must not consume the already-claimed nonce.
    first = cargar_propuesta_autorizada(path, cycle)
    second = cargar_propuesta_autorizada(path, cycle)
    assert first["authorization"]["identity_verified"] is True
    assert second["authorization"]["approver"] == "real-test-owner"

    nonce_ledger = tmp_path / "state" / "approver_nonces.jsonl"
    assert len(nonce_ledger.read_text().splitlines()) == 1

    # CX-03: el ledger es inmutable con hash chain. Manipular el flag
    # sin actualizar el hash debe bloquear, no ser tolerado. La firma
    # ya no basta si la historia fue reescrita.
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[-1]["payload"]["identity_verified"] = False
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    import pytest as _pt
    with _pt.raises(PermissionError, match="Ledger corrupto"):
        cargar_propuesta_autorizada(path, cycle)

    # A valid signature inserted without its original atomic nonce claim is not dispatchable.
    nonce_contents = nonce_ledger.read_text()
    nonce_ledger.write_text("")
    # CX-03: el ledger sigue corrupto del paso anterior, asi que el bloqueo puede ser por hash o por nonce. Ambos son fail-closed valido.
    with pytest.raises(PermissionError, match="Ledger corrupto|no verificable"):
        cargar_propuesta_autorizada(path, cycle)
    nonce_ledger.write_text(nonce_contents)

    # Changing the pre-authorization evidence must invalidate the signed digest.
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[2]["payload"]["proposal"] = "silently changed proposal"
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    with pytest.raises(PermissionError, match="Ledger corrupto|no verificable"):
        cargar_propuesta_autorizada(path, cycle)

    # A mismatched purpose must fail even when the signature itself is valid.
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[2]["payload"]["proposal"] = proposal_payload["proposal"]
    tampered = dict(assertion)
    tampered["purpose"] = "catedralx_financial_order_authorization"
    tampered["signature"] = private_key.sign(
        ordenes._canonical_json_ed25519(tampered)
    ).hex()
    rows[-1]["payload"]["identity_assertion"] = tampered
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    with pytest.raises(PermissionError, match="Ledger corrupto|no verificable"):
        cargar_propuesta_autorizada(path, cycle)
