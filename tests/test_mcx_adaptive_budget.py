import pytest

from ENERGY.resource_governor import energy_budget_snapshot
from FEX.FEEDBACK.feedback_loop import registrar_prediccion
from MCX.OPTIMIZE.ganancias import financiar_analisis_adaptativo


def configure(monkeypatch, tmp_path, *, adaptive_initial="5", adaptive_reserve="1"):
    monkeypatch.setenv("CATEDRALX_ENERGY_LEDGER_PATH", str(tmp_path / "energy.jsonl"))
    monkeypatch.setenv("CATEDRALX_ENERGY_OPERATIONAL_CAPACITY", "10")
    monkeypatch.setenv("CATEDRALX_ENERGY_ADAPTIVE_CAPACITY", "5")
    monkeypatch.setenv("CATEDRALX_ENERGY_OPERATIONAL_INITIAL", "10")
    monkeypatch.setenv("CATEDRALX_ENERGY_ADAPTIVE_INITIAL", adaptive_initial)
    monkeypatch.setenv("CATEDRALX_ENERGY_MAX_DISCHARGE", "2")
    monkeypatch.setenv("CATEDRALX_ENERGY_OPERATIONAL_RESERVE", "2")
    monkeypatch.setenv("CATEDRALX_ENERGY_ADAPTIVE_RESERVE", adaptive_reserve)


def prediction(feedback_path):
    return registrar_prediccion(
        {
            "decision": "buy",
            "reference_price": 100.0,
            "observed_at": "2026-01-01T00:00:00+00:00",
            "market_source": "test-feed",
        },
        path=feedback_path,
        prediction_id="prediction-verified-1",
    )


def observed_outcome():
    return {
        "observed_price": 101.0,
        "observed_at": "2026-01-01T00:01:00+00:00",
        "source": "test-feed",
    }


def test_verified_observed_outcome_authorizes_adaptive_budget(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    feedback_path = tmp_path / "feedback.jsonl"
    prediction(feedback_path)

    result = financiar_analisis_adaptativo(
        prediction_id="prediction-verified-1",
        horizon="1m",
        outcome=observed_outcome(),
        feedback_path=feedback_path,
        amount=1,
    )

    assert result["status"] == "ADAPTIVE_ANALYSIS_AUTHORIZED"
    assert result["credits_spent"] == 1
    assert result["unit"] == "virtual_compute_credit"
    assert result["orders_executed"] is False
    assert energy_budget_snapshot()["adaptive"].charge == 4


def test_hypothetical_or_early_outcome_does_not_spend_adaptive_budget(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    feedback_path = tmp_path / "feedback.jsonl"
    prediction(feedback_path)
    early = observed_outcome()
    early["observed_at"] = "2026-01-01T00:00:30+00:00"

    with pytest.raises(ValueError, match="Horizonte aún no vencido"):
        financiar_analisis_adaptativo(
            prediction_id="prediction-verified-1",
            horizon="1m",
            outcome=early,
            feedback_path=feedback_path,
            amount=1,
        )

    assert energy_budget_snapshot()["adaptive"].charge == 5


def test_missing_adaptive_budget_fails_closed(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, adaptive_initial="1", adaptive_reserve="1")
    feedback_path = tmp_path / "feedback.jsonl"
    prediction(feedback_path)

    with pytest.raises(ValueError, match="Reserva insuficiente"):
        financiar_analisis_adaptativo(
            prediction_id="prediction-verified-1",
            horizon="1m",
            outcome=observed_outcome(),
            feedback_path=feedback_path,
            amount=1,
        )

    assert energy_budget_snapshot()["adaptive"].charge == 1
