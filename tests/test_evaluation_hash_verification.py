"""C-2: evaluation_hash must be verifiable by recomputation in CatedralX.

Agents only validates the hash by format. These tests cover the two hash
schemes CatedralX produces (central multicriteria verdict and opportunity
evaluation) plus the `verify-evaluation-hash` CLI entry point.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from REASON.core_contract import (
    evaluate_economic_opportunity,
    verify_opportunity_evaluation_hash,
)
from REASON.multicriteria import (
    CathedralEvaluation,
    verify_evaluation_hash,
)

ROOT = Path(__file__).resolve().parents[1]


def _central_result(**overrides):
    evaluation = CathedralEvaluation(
        viability=9000, human_value=9000, distribution=9000,
        reinvestment="1500.00", resilience=9000, evidence=9500,
    )
    result = evaluation.evaluate()
    result.update(overrides)
    return result


def _opportunity_payload():
    digest = hashlib.sha256(b"fixture-evidence").hexdigest()
    return {
        "opportunity_id": "opp-001",
        "name": "Servicio digital piloto",
        "category": "digital_service",
        "income_model": "hybrid",
        "currency": "MXN",
        "horizon_months": 12,
        "capital_required": 5000,
        "available_capital": 3000,
        "revenue": [{"amount": 2000, "frequency": "monthly", "evidence_id": "ev-1"}],
        "costs": [{"amount": 500, "frequency": "monthly", "evidence_id": "ev-1"}],
        "evidence": [{
            "evidence_id": "ev-1", "source": "user_supplied_estimate",
            "observed_at": datetime.now(UTC).isoformat(), "digest": digest,
        }],
        "assumptions": ["La facturación mensual estimada se mantiene durante el horizonte."],
        "scenarios": [
            {"name": "conservative", "revenue_multiplier": 0.7, "cost_multiplier": 1.2},
            {"name": "base", "revenue_multiplier": 1.0, "cost_multiplier": 1.0},
            {"name": "optimistic", "revenue_multiplier": 1.2, "cost_multiplier": 0.9},
        ],
        "trace_id": "1234567890abcdef1234567890abcdef",
    }


# --- central multicriteria hash ---------------------------------------------

def test_central_hash_verifies_for_a_fresh_evaluation():
    result = _central_result()
    assert result["status"] == "ACCEPTED"
    report = verify_evaluation_hash(result)
    assert report == {
        "valid": True, "kind": "central", "expected": result["evaluation_hash"],
        "computed": result["evaluation_hash"], "reason": "ok",
    }


def test_central_hash_rejects_tampered_score():
    result = _central_result()
    tampered = copy.deepcopy(result)
    tampered["score"] = 10000
    report = verify_evaluation_hash(tampered)
    assert report["valid"] is False
    assert report["reason"] == "hash_mismatch"
    assert report["computed"] != result["evaluation_hash"]


def test_central_hash_rejects_tampered_dimensions():
    result = _central_result()
    tampered = copy.deepcopy(result)
    tampered["dimensions"]["viability"] = 10000
    assert verify_evaluation_hash(tampered)["valid"] is False


def test_central_hash_rejects_tampered_status():
    result = _central_result()
    tampered = copy.deepcopy(result)
    tampered["status"] = "REJECTED"
    assert verify_evaluation_hash(tampered)["valid"] is False


def test_central_hash_rejects_forged_hash():
    result = _central_result()
    forged = copy.deepcopy(result)
    forged["evaluation_hash"] = "0" * 64
    report = verify_evaluation_hash(forged)
    assert report["valid"] is False
    assert report["reason"] == "hash_mismatch"
    assert report["expected"] == "0" * 64


def test_central_hash_rejects_missing_hash():
    result = _central_result()
    stripped = {k: v for k, v in result.items() if k != "evaluation_hash"}
    report = verify_evaluation_hash(stripped)
    assert report["valid"] is False
    assert report["reason"] == "missing_expected_hash"


def test_central_hash_verifies_against_explicit_expected():
    result = _central_result()
    stripped = {k: v for k, v in result.items() if k != "evaluation_hash"}
    assert verify_evaluation_hash(stripped, expected=result["evaluation_hash"])["valid"] is True
    assert verify_evaluation_hash(stripped, expected="f" * 64)["valid"] is False


def test_central_hash_verifies_blocked_evaluations_too():
    evaluation = CathedralEvaluation(
        viability=9000, human_value=9000, distribution=9000,
        reinvestment="1500.00", resilience=9000, evidence=1000,
    )
    result = evaluation.evaluate()
    assert result["status"] == "BLOCKED_EVIDENCE"
    assert verify_evaluation_hash(result)["valid"] is True


def test_central_verify_never_raises_for_bad_input():
    assert verify_evaluation_hash(None)["valid"] is False  # type: ignore[arg-type]
    assert verify_evaluation_hash({"evaluation_hash": 123})["valid"] is False


# --- opportunity hash -------------------------------------------------------

def test_opportunity_hash_verifies_for_a_fresh_evaluation():
    result = evaluate_economic_opportunity(_opportunity_payload())
    report = verify_opportunity_evaluation_hash(result)
    assert report["valid"] is True
    assert report["kind"] == "opportunity"
    assert report["computed"] == result["evaluation_hash"]


def test_opportunity_hash_rejects_tampered_scenario():
    result = evaluate_economic_opportunity(_opportunity_payload())
    tampered = copy.deepcopy(result)
    tampered["scenarios"]["base"]["net_result"] = 999999.0
    assert verify_opportunity_evaluation_hash(tampered)["valid"] is False


def test_opportunity_hash_rejects_tampered_decision_candidate():
    result = evaluate_economic_opportunity(_opportunity_payload())
    tampered = copy.deepcopy(result)
    tampered["decision_candidate"] = "PURSUE"
    assert verify_opportunity_evaluation_hash(tampered)["valid"] is False


def test_opportunity_hash_rejects_forged_hash():
    result = evaluate_economic_opportunity(_opportunity_payload())
    forged = copy.deepcopy(result)
    forged["evaluation_hash"] = "a" * 64
    report = verify_opportunity_evaluation_hash(forged)
    assert report["valid"] is False
    assert report["reason"] == "hash_mismatch"


# --- CLI --------------------------------------------------------------------

def _run_cli(path: Path, *extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CATEDRALX_PYTHON"] = sys.executable
    return subprocess.run(
        ["bash", str(ROOT / "BIN/catedral"), "verify-evaluation-hash",
         "--input-file", str(path), *extra],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=15, check=False,
    )


def test_cli_accepts_valid_central_evaluation(tmp_path):
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(_central_result()), encoding="utf-8")
    completed = _run_cli(path)
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["valid"] is True
    assert report["kind"] == "central"


def test_cli_rejects_tampered_central_evaluation(tmp_path):
    tampered = _central_result()
    tampered["score"] = 0
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    completed = _run_cli(path)
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["reason"] == "hash_mismatch"


def test_cli_accepts_valid_opportunity_evaluation(tmp_path):
    result = evaluate_economic_opportunity(_opportunity_payload())
    path = tmp_path / "opportunity.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    completed = _run_cli(path)
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["valid"] is True
    assert report["kind"] == "opportunity"


def test_cli_rejects_tampered_opportunity_evaluation(tmp_path):
    result = evaluate_economic_opportunity(_opportunity_payload())
    result["scenarios"]["base"]["net_result"] = 1.0
    path = tmp_path / "opportunity.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    completed = _run_cli(path)
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["valid"] is False


def test_cli_honors_explicit_kind_and_expected(tmp_path):
    result = _central_result()
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    assert _run_cli(path, "--kind", "central").returncode == 0
    assert _run_cli(path, "--kind", "opportunity").returncode == 1
    assert _run_cli(path, "--expected", result["evaluation_hash"]).returncode == 0
    assert _run_cli(path, "--expected", "0" * 64).returncode == 1


def test_cli_returns_2_for_missing_file(tmp_path):
    completed = _run_cli(tmp_path / "missing.json")
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["reason"] == "input_file_not_found"


def test_cli_returns_2_for_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    completed = _run_cli(path)
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["reason"].startswith("input_unreadable")


def test_cli_returns_2_for_unknown_evaluation_kind(tmp_path):
    path = tmp_path / "other.json"
    path.write_text(json.dumps({"engine": "CatedralX", "status": "ANALYSIS_COMPLETE"}), encoding="utf-8")
    completed = _run_cli(path)
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["reason"] == "unknown_evaluation_kind"


# --- DecisionResult expone la evaluación (cableado Agents, liberación) ------

def test_decision_result_exposes_evaluation_for_independent_verification(tmp_path):
    """El DecisionResult debe llevar el veredicto crudo para recomputar el hash.

    Sin este campo, Agents no puede verificar `evaluation_hash` en la ruta
    general: la salida del CLI `motor` solo lleva el hash, no el objeto
    evaluado. Con el campo, la verificación es recomputo real vía el CLI.
    """
    from types import SimpleNamespace

    from elite.contracts.builder import build_decision_result

    verdict = _central_result()
    state = SimpleNamespace(
        decision="buy",
        percepcion_espacial={
            "cycle_id": "test-cycle-c2",
            "analisis_financiero": {"risk_flags": []},
        },
    )
    cognitive = {
        "coherencia": {"disonancia": 0.0},
        "contraevidencia": {"fuerza_contra": 0.0},
        "provenance": [{
            "id": "SCX:fixture:1:aaaaaaaaaaaaaaaa",
            "modulo": "tests.synthetic_fixture",
            "input_hash": "a" * 64,
            "timestamp": 1735689600,
            "status": "synthetic_test_evidence",
        }],
        "cathedral_verdict": verdict,
    }
    decision = build_decision_result(
        state, cognitive, trace_id="1234567890abcdef1234567890abcdef"
    )
    assert decision["status"] == "ACCEPTED"
    assert decision["evaluation"] == verdict
    assert verify_evaluation_hash(decision["evaluation"])["valid"] is True

    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(decision["evaluation"]), encoding="utf-8")
    completed = _run_cli(path, "--kind", "central")
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["valid"] is True


def test_decision_result_evaluation_survives_tamper_detection(tmp_path):
    """Manipular la evaluación expuesta debe invalidar el hash (no es decorativa)."""
    from types import SimpleNamespace

    from elite.contracts.builder import build_decision_result

    verdict = _central_result()
    state = SimpleNamespace(
        decision="buy",
        percepcion_espacial={
            "cycle_id": "test-cycle-c2",
            "analisis_financiero": {"risk_flags": []},
        },
    )
    cognitive = {
        "coherencia": {"disonancia": 0.0},
        "contraevidencia": {"fuerza_contra": 0.0},
        "provenance": [{
            "id": "SCX:fixture:1:aaaaaaaaaaaaaaaa",
            "modulo": "tests.synthetic_fixture",
            "input_hash": "a" * 64,
            "timestamp": 1735689600,
            "status": "synthetic_test_evidence",
        }],
        "cathedral_verdict": verdict,
    }
    decision = build_decision_result(
        state, cognitive, trace_id="1234567890abcdef1234567890abcdef"
    )
    tampered = dict(decision["evaluation"])
    tampered["score"] = 0
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    completed = _run_cli(path, "--kind", "central")
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["reason"] == "hash_mismatch"
