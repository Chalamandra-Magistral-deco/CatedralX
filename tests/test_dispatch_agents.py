import base64
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "elite" / "bin" / "dispatch_agents.py"
SPEC = importlib.util.spec_from_file_location("dispatch_agents", SCRIPT)
dispatch_agents = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(dispatch_agents)


def decode_segment(segment: str) -> dict:
    padding = "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment + padding))


class FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"run_id":"run-test-1","status":"queued","trace_id":"trace-test-1"}'


def test_dispatch_task_posts_payload_with_scoped_short_lived_jwt(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.headers["Authorization"]
        captured["idempotency_key"] = request.headers.get("Idempotency-key")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(dispatch_agents, "urlopen", fake_urlopen)
    payload = {
        "historical_prices": [100.0 + index * 0.01 for index in range(30)],
        "current_price": 100.29,
        "observed_at": "2026-10-27T20:00:00+00:00",
        "source": "test_fixture",
    }
    result = dispatch_agents.dispatch_task(
        "financial_analysis",
        payload,
        "http://127.0.0.1:8766",
        "a-long-test-only-jwt-secret",
        timeout=3,
        idempotency_key="catedralx-cycle-test-1",
    )

    assert result["status"] == "queued"
    assert captured["url"] == "http://127.0.0.1:8766/internal/v1/orchestration/runs"
    assert captured["body"]["payload"] == payload
    assert captured["body"]["objective"] == "financial_analysis"
    assert captured["idempotency_key"] == "catedralx-cycle-test-1"

    token = captured["authorization"].removeprefix("Bearer ")
    header = decode_segment(token.split(".")[0])
    claims = decode_segment(token.split(".")[1])
    assert header == {"alg": "HS256", "typ": "JWT"}
    assert claims["scope"] == "orchestration:run"
    assert claims["sub"] == "catedralx-service"
    assert claims["exp"] - claims["iat"] == 60


def test_dispatch_requires_jwt_secret():
    with pytest.raises(ValueError, match="CHALAMANDRA_JWT_SECRET"):
        dispatch_agents.dispatch_task(
            "financial_analysis", {}, "http://127.0.0.1:8766", ""
        )


def test_dispatch_rejects_non_loopback_plain_http():
    with pytest.raises(ValueError, match="loopback"):
        dispatch_agents._validate_api_url("http://8.8.8.8:8766")


def test_dispatch_rejects_url_credentials():
    with pytest.raises(ValueError, match="no admite credenciales"):
        dispatch_agents._validate_api_url("http://user:pass@127.0.0.1:8766")


def _write_approved_cycle(path: Path, cycle_id: str, *, approved: bool = True) -> None:
    events = [
        ("measure", {
            "metric": "qualified_leads",
            "source": "crm_export_test",
            "period": "2026-10",
            "unit": "leads",
            "formula": "count_unique",
            "value": 12,
            "observed_at": "2026-10-27T12:00:00Z",
        }),
        ("evaluate", {
            "assessment": "Volumen insuficiente para el objetivo",
            "evidence": "crm_export_test; muestra sintética",
        }),
        ("propose", {
            "proposal": "Analizar las consultas y objeciones para priorizar una página de producto",
            "expected_outcome": "Generar un candidato de mejora respaldado por evidencia",
            "verification_plan": "Comparar leads cualificados por fuente antes y después",
        }),
        ("authorize", {
            "approved": approved,
            "approver": "owner-test",
            "rationale": "Prueba aislada; solo análisis y generación de candidatos",
        }),
    ]
    path.write_text(
        "".join(
            json.dumps({
                "schema_version": 1,
                "event_id": f"event-{index}",
                "cycle_id": cycle_id,
                "event_type": kind,
                "payload": payload,
            }) + "\n"
            for index, (kind, payload) in enumerate(events)
        ),
        encoding="utf-8",
    )


def test_load_authorized_proposal_from_catedralx_ledger(tmp_path):
    ledger = tmp_path / "impact.jsonl"
    _write_approved_cycle(ledger, "cycle-approved")

    proposal = dispatch_agents.load_authorized_proposal(ledger, "cycle-approved")

    assert proposal["origin"] == "CatedralX.FEX.GOVERNANCE.economic_cycle"
    assert proposal["cycle_id"] == "cycle-approved"
    assert proposal["proposal"]["expected_outcome"].startswith("Generar")
    assert proposal["authorization"]["approved"] is True
    assert proposal["execution_boundary"]["independent_acceptance_required"] is True
    assert "ad_spend" in proposal["execution_boundary"]["prohibited"]


def test_load_proposal_fails_closed_without_human_approval(tmp_path):
    ledger = tmp_path / "impact.jsonl"
    _write_approved_cycle(ledger, "cycle-pending", approved=False)

    with pytest.raises(ValueError, match="autorización humana"):
        dispatch_agents.load_authorized_proposal(ledger, "cycle-pending")


def test_load_proposal_rejects_cycle_after_authorize_or_missing_stages(tmp_path):
    ledger = tmp_path / "impact.jsonl"
    _write_approved_cycle(ledger, "cycle-approved")
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "schema_version": 1,
            "event_id": "event-5",
            "cycle_id": "cycle-approved",
            "event_type": "verify",
            "payload": {"result": "already verified"},
        }) + "\n")

    with pytest.raises(ValueError, match="sin etapas adicionales"):
        dispatch_agents.load_authorized_proposal(ledger, "cycle-approved")
