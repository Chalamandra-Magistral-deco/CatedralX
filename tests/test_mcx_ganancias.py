from __future__ import annotations

import json
import math

import pytest

from MCX.OPTIMIZE.ganancias import (
    factor_profit,
    ledger_path,
    maximo_drawdown,
    pnl,
    registrar_resultado,
    rendimiento_esperado,
    rendimiento_porcentaje,
    sharpe_ratio,
    tasa_acierto,
)


def test_percentage_return_and_pnl():
    assert rendimiento_porcentaje(100, 115) == pytest.approx(15.0)
    assert pnl(100, 115, 2) == pytest.approx(30.0)
    with pytest.raises(ValueError):
        rendimiento_porcentaje(0, 100)


def test_win_rate_and_expected_value():
    assert tasa_acierto(7, 10) == pytest.approx(70.0)
    assert tasa_acierto(0, 0) == 0.0
    assert rendimiento_esperado(60, 20, 10) == pytest.approx(8.0)


def test_profit_factor_and_drawdown():
    assert factor_profit([10, 5], [-3, -2]) == pytest.approx(3.0)
    assert factor_profit([10], []) == math.inf
    assert factor_profit([], []) == 0.0
    assert maximo_drawdown([100, 120, 90, 110]) == pytest.approx(25.0)
    assert maximo_drawdown([100]) == 0.0


def test_sharpe_ratio():
    assert sharpe_ratio([1.0, 2.0, 3.0]) == pytest.approx(
        2.0 / math.sqrt(2.0 / 3.0)
    )
    assert sharpe_ratio([1.0, 1.0]) == 0.0
    assert sharpe_ratio([1.0]) == 0.0


def test_append_only_ledger_marks_no_order_execution(tmp_path):
    target = tmp_path / "ledger.jsonl"
    result = registrar_resultado({"pnl": 12.5, "decision": "hold"}, path=target)
    assert result == target
    row = json.loads(target.read_text(encoding="utf-8"))
    assert row["pnl"] == 12.5
    assert row["orders_executed_by_this_module"] is False
