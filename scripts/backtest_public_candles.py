#!/usr/bin/env python3
"""Offline, analysis-only evaluation of CatedralX signals on public BTC/USDT candles.

Fetches historical public spot candles, evaluates each signal against a fixed future
horizon, and prints a JSON report. It never submits orders or simulates account P&L.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
ELITE = ROOT / "elite"
if str(ELITE) not in sys.path:
    sys.path.insert(0, str(ELITE))

from REASON.financial_engine import analyze_financial_market

ENDPOINT = "https://data-api.binance.vision/api/v3/klines"
INTERVAL = "1m"
INTERVAL_MS = 60_000
PAGE_LIMIT = 1000
MIN_WINDOW = 60
SIGNALS = ("buy", "sell", "hold")


def utc_iso(milliseconds: int) -> str:
    return datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc).isoformat()


def fetch_history(symbol: str = "BTCUSDT", days: int = 7, timeout: float = 10.0) -> list[dict[str, Any]]:
    """Fetch closed, contiguous historical 1-minute candles, failing closed on gaps."""
    if not symbol.isalnum() or not 5 <= len(symbol) <= 20 or symbol.upper() != symbol:
        raise ValueError("symbol must be uppercase alphanumeric (e.g. BTCUSDT)")
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 30:
        raise ValueError("days must be an integer from 1 to 30")
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - days * 24 * 60 * 60 * 1000
    cursor = start_ms
    raw_rows: list[list[Any]] = []
    while cursor < now_ms:
        query = urlencode({
            "symbol": symbol,
            "interval": INTERVAL,
            "startTime": cursor,
            "endTime": now_ms,
            "limit": PAGE_LIMIT,
        })
        request = Request(
            f"{ENDPOINT}?{query}",
            headers={"Accept": "application/json", "User-Agent": "CatedralX-Offline-Evaluation/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=timeout) as response:
            if getattr(response, "status", 200) != 200:
                raise RuntimeError(f"market provider returned HTTP {response.status}")
            batch = json.loads(response.read(2_000_000).decode("utf-8"))
        if not isinstance(batch, list):
            raise ValueError("market provider did not return a list of candles")
        if not batch:
            break
        raw_rows.extend(batch)
        try:
            last_open = int(batch[-1][0])
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError("invalid candle timestamp returned by provider") from exc
        next_cursor = last_open + INTERVAL_MS
        if next_cursor <= cursor:
            raise ValueError("provider pagination did not advance; aborting")
        cursor = next_cursor
        if len(batch) < PAGE_LIMIT:
            break

    unique: dict[int, dict[str, Any]] = {}
    for index, row in enumerate(raw_rows):
        if not isinstance(row, (list, tuple)) or len(row) < 7:
            raise ValueError(f"candle {index} has an invalid shape")
        try:
            opened = int(row[0])
            open_price = float(row[1])
            high_price = float(row[2])
            low_price = float(row[3])
            close_price = float(row[4])
            volume = float(row[5])
            closed = int(row[6])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"candle {index} contains invalid values") from exc
        values = (open_price, high_price, low_price, close_price, volume)
        if not all(math.isfinite(v) for v in values) or min(open_price, high_price, low_price, close_price) <= 0 or volume < 0:
            raise ValueError(f"candle {index} contains non-finite/invalid numeric values")
        # Include only bars fully inside requested time span and already closed.
        if opened < start_ms or closed >= now_ms:
            continue
        unique[opened] = {
            "open_time_ms": opened,
            "close_time_ms": closed,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        }
    candles = [unique[key] for key in sorted(unique)]
    if len(candles) < MIN_WINDOW + 10:
        raise ValueError(f"too few closed candles for evaluation: {len(candles)}")
    for previous, current in zip(candles, candles[1:]):
        delta = current["open_time_ms"] - previous["open_time_ms"]
        if delta != INTERVAL_MS:
            raise ValueError(
                f"missing/duplicated 1-minute candle between {utc_iso(previous['open_time_ms'])} "
                f"and {utc_iso(current['open_time_ms'])}; no candles were interpolated"
            )
    return candles


def future_label(return_pct: float, threshold_pct: float) -> str:
    if return_pct >= threshold_pct:
        return "buy"
    if return_pct <= -threshold_pct:
        return "sell"
    return "hold"


def score_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    confusion = {pred: {actual: 0 for actual in SIGNALS} for pred in SIGNALS}
    for row in rows:
        confusion[row["predicted"]][row["actual"]] += 1
    count = len(rows)
    correct = sum(confusion[signal][signal] for signal in SIGNALS)
    directional = [row for row in rows if row["predicted"] in {"buy", "sell"}]
    wins = [row for row in directional if (row["forward_return_pct"] > 0 if row["predicted"] == "buy" else row["forward_return_pct"] < 0)]
    aligned_returns = [row["forward_return_pct"] if row["predicted"] == "buy" else -row["forward_return_pct"] for row in directional]
    return {
        "samples": count,
        "classification_accuracy": round(correct / count, 6) if count else None,
        "always_hold_accuracy_baseline": round(sum(row["actual"] == "hold" for row in rows) / count, 6) if count else None,
        "directional_signal_coverage": round(len(directional) / count, 6) if count else None,
        "directional_gross_sign_hit_rate": round(len(wins) / len(directional), 6) if directional else None,
        "mean_direction_aligned_forward_return_pct_before_costs": round(statistics.fmean(aligned_returns), 8) if aligned_returns else None,
        "confusion_matrix_predicted_rows_actual_columns": confusion,
        "per_class": {
            signal: {
                "precision": round(confusion[signal][signal] / sum(confusion[signal].values()), 6) if sum(confusion[signal].values()) else None,
                "recall": round(confusion[signal][signal] / sum(confusion[pred][signal] for pred in SIGNALS), 6) if sum(confusion[pred][signal] for pred in SIGNALS) else None,
                "actual_support": sum(confusion[pred][signal] for pred in SIGNALS),
            }
            for signal in SIGNALS
        },
    }


def evaluate(candles: list[dict[str, Any]], horizon: int = 5, threshold_pct: float = 0.05) -> dict[str, Any]:
    if isinstance(horizon, bool) or not isinstance(horizon, int) or not 1 <= horizon <= 60:
        raise ValueError("horizon must be an integer from 1 to 60 minutes")
    if not math.isfinite(threshold_pct) or threshold_pct <= 0:
        raise ValueError("threshold_pct must be positive and finite")
    closes = [float(candle["close"]) for candle in candles]
    rows: list[dict[str, Any]] = []
    # At each close, classify using only the preceding 60 closed prices; the
    # outcome is measured strictly after that close, over the requested horizon.
    for index in range(MIN_WINDOW - 1, len(closes) - horizon):
        history = closes[index - MIN_WINDOW + 1:index + 1]
        result = analyze_financial_market(history)
        forward_return = (closes[index + horizon] / closes[index] - 1.0) * 100.0
        rows.append({
            "timestamp_ms": candles[index]["close_time_ms"],
            "predicted": result["signal"],
            "actual": future_label(forward_return, threshold_pct),
            "forward_return_pct": forward_return,
        })
    if len(rows) < 20:
        raise ValueError("too few evaluated predictions")
    split = len(rows) // 2
    half1, half2 = rows[:split], rows[split:]
    return {
        "report_type": "CatedralX historical signal evaluation (not trading P&L)",
        "market_data": {
            "provider": "Binance public spot market-data endpoint",
            "symbol": "BTCUSDT",
            "interval": INTERVAL,
            "first_candle_open_utc": utc_iso(candles[0]["open_time_ms"]),
            "last_candle_close_utc": utc_iso(candles[-1]["close_time_ms"]),
            "closed_candles": len(candles),
        },
        "evaluation": {
            "lookback_candles": MIN_WINDOW,
            "forward_horizon_minutes": horizon,
            "future_label_threshold_pct": threshold_pct,
            "predictions_evaluated": len(rows),
            "chronological_halves_are_diagnostic_not_parameter_train_test": True,
        },
        "all_period": score_rows(rows),
        "first_chronological_half": {
            "from_utc": utc_iso(half1[0]["timestamp_ms"]),
            "to_utc": utc_iso(half1[-1]["timestamp_ms"]),
            **score_rows(half1),
        },
        "second_chronological_half": {
            "from_utc": utc_iso(half2[0]["timestamp_ms"]),
            "to_utc": utc_iso(half2[-1]["timestamp_ms"]),
            **score_rows(half2),
        },
        "safety": {
            "analysis_only": True,
            "orders_created": False,
            "orders_executed": False,
            "trading_enabled": False,
            "fees_slippage_funding_and_spread_included": False,
            "real_account_pnl_calculated": False,
        },
        "limitations": [
            "Signals are heuristic labels; this report does not establish profitability or future performance.",
            "The forward label threshold is an evaluation convention, not a trading rule.",
            "Mean direction-aligned returns are gross descriptive statistics before costs and do not represent portfolio P&L.",
            "Chronological halves are stability diagnostics only; no parameters were trained or tuned.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="BTCUSDT", help="Public spot symbol (default BTCUSDT)")
    parser.add_argument("--days", type=int, default=7, help="History window, 1-30 days (default 7)")
    parser.add_argument("--horizon-minutes", type=int, default=5, help="Forward evaluation horizon (default 5)")
    parser.add_argument("--threshold-pct", type=float, default=0.05, help="Future-return class threshold in percent (default 0.05)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Network timeout per request in seconds")
    parser.add_argument("--compare-horizons", action="store_true", help="Also compare 1, 5, 15, 30 and 60 minute outcomes using the same downloaded candles")
    parser.add_argument("--output", help="Optional report JSON path; default prints report only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        candles = fetch_history(args.symbol, args.days, args.timeout)
        report = evaluate(candles, args.horizon_minutes, args.threshold_pct)
        if args.compare_horizons:
            comparison = {}
            for horizon in (1, 5, 15, 30, 60):
                evaluated = evaluate(candles, horizon, args.threshold_pct)
                comparison[str(horizon)] = {
                    "horizon_minutes": horizon,
                    "all_period": evaluated["all_period"],
                    "first_chronological_half": evaluated["first_chronological_half"],
                    "second_chronological_half": evaluated["second_chronological_half"],
                }
            report["horizon_comparison"] = comparison
    except Exception as exc:
        print(json.dumps({
            "status": "EVALUATION_FAILED",
            "error_type": type(exc).__name__,
            "reason": str(exc),
            "trading_enabled": False,
            "orders_created": False,
            "orders_executed": False,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        from pathlib import Path
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded + "\n", encoding="utf-8")
        print(json.dumps({
            "status": "EVALUATION_COMPLETE",
            "report_path": str(output_path),
            "evaluated_predictions": report["evaluation"]["predictions_evaluated"],
            "trading_enabled": False,
            "orders_created": False,
            "orders_executed": False,
        }, ensure_ascii=False, indent=2))
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
