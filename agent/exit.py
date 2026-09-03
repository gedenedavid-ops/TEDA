"""
Position exit monitor — auto TP / SL.

Tracks every opened spread in logs/positions.json and closes positions
when the underlying price reaches the stop-loss or take-profit level.

Usage:
    from agent.exit import check_and_exit
    check_and_exit(broker)   # run at the start of every agent loop
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from alpaca.trading.enums import OrderSide, PositionIntent, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from execution.client import BrokerClient

TRACKER_PATH = Path(__file__).resolve().parent.parent / "logs" / "positions.json"


# ---- Persistence ---------------------------------------------------------


def load_positions() -> List[Dict[str, Any]]:
    """Load the position tracker from disk."""
    if not TRACKER_PATH.exists():
        return []
    with open(TRACKER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_positions(positions: List[Dict[str, Any]]) -> None:
    """Persist the position tracker."""
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_PATH, "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=2, default=str)


# ---- Track a new position ------------------------------------------------


def track_position(
    order_id: str,
    symbol: str,
    signal_str: str,
    stop_loss: Optional[float],
    take_profit: Optional[float],
    leg_symbols: List[str],
) -> None:
    """Record a newly opened spread so the exit monitor can manage it."""
    positions = load_positions()
    positions.append(
        {
            "order_id": order_id,
            "symbol": symbol,
            "signal": signal_str,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "legs": leg_symbols,
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "closed": False,
        }
    )
    save_positions(positions)
    print(f"  [exit] position tracked: {order_id} ({symbol})")


# ---- Check and close -----------------------------------------------------


def check_and_exit(broker: BrokerClient) -> int:
    """Check all tracked positions and close any that hit SL or TP.

    Returns the number of positions closed.
    """
    positions = load_positions()
    closed_count = 0
    updated = False

    for pos in positions:
        if pos.get("closed"):
            continue

        symbol = pos["symbol"]
        sl = pos.get("stop_loss")
        tp = pos.get("take_profit")

        if sl is None and tp is None:
            continue

        current_price = _fetch_current_price(broker, symbol)
        if current_price is None:
            continue

        reason = _should_close(pos["signal"], current_price, sl, tp)
        if reason is None:
            continue

        success = _close_spread(broker, pos, reason, current_price)
        if success:
            pos["closed"] = True
            pos["closed_at"] = datetime.now(timezone.utc).isoformat()
            pos["close_reason"] = reason
            pos["close_price"] = current_price
            closed_count += 1
            updated = True

    if updated:
        save_positions(positions)

    return closed_count


# ---- Helpers -------------------------------------------------------------


def _fetch_current_price(broker: BrokerClient, symbol: str) -> Optional[float]:
    """Get the latest close from 1H bars (works intraday)."""
    from data.market_data import fetch_stock_bars

    df = fetch_stock_bars(broker.stock_data, symbol, "1H", limit=5)
    if df.empty:
        return None
    return float(df["close"].iloc[-1])


def _should_close(
    signal: str, price: float, sl: Optional[float], tp: Optional[float]
) -> Optional[str]:
    """Return 'SL', 'TP', or None if neither is hit."""
    if signal == "BUY":
        if sl is not None and price <= sl:
            return "SL"
        if tp is not None and price >= tp:
            return "TP"
    else:  # SELL
        if sl is not None and price >= sl:
            return "SL"
        if tp is not None and price <= tp:
            return "TP"
    return None


def _close_spread(
    broker: BrokerClient, pos: Dict[str, Any], reason: str, price: float
) -> bool:
    """Close every leg of the spread individually.

    Debit spread legs:
      - Leg 0 (long)  : BTO → need STC (sell to close)
      - Leg 1 (short) : STO → need BTC (buy to close)
    """
    symbol = pos["symbol"]
    legs = pos.get("legs", [])
    if not legs:
        print(f"  [exit] pas de jambes trouvées pour {pos['order_id']} — skip")
        return False

    print(f"\n  [exit] CLÔTURE {reason} | {symbol} @ {price:.2f}")
    all_ok = True

    for i, leg_sym in enumerate(legs):
        # Leg 0 = long (BTO), Leg 1 = short (STO)
        if i == 0:
            closing_side = OrderSide.SELL
            closing_intent = PositionIntent.SELL_TO_CLOSE
        else:
            closing_side = OrderSide.BUY
            closing_intent = PositionIntent.BUY_TO_CLOSE

        try:
            order = MarketOrderRequest(
                symbol=leg_sym,
                qty=1,
                side=closing_side,
                time_in_force=TimeInForce.DAY,
                position_intent=closing_intent,
            )
            result = broker.submit_order(order)
            print(f"       fermé {leg_sym} | {result.id}")
        except Exception as exc:
            print(f"       ÉCHEC {leg_sym} : {exc}")
            all_ok = False

    return all_ok


# ---- Summary -------------------------------------------------------------


def has_open_position(symbol: str) -> bool:
    """Return True if there's an open tracked position for this symbol."""
    positions = load_positions()
    return any(
        not p.get("closed") and p.get("symbol") == symbol
        for p in positions
    )


def open_count() -> int:
    """How many positions are still open?"""
    positions = load_positions()
    return sum(1 for p in positions if not p.get("closed"))


def print_summary() -> None:
    """Print a one-line summary of tracked positions."""
    positions = load_positions()
    open_positions = [p for p in positions if not p.get("closed")]
    closed_positions = [p for p in positions if p.get("closed")]

    if not positions:
        print("  [exit] aucune position trackée.")
        return

    print(
        f"  [exit] {len(open_positions)} ouverte(s), "
        f"{len(closed_positions)} fermée(s)"
    )
    for p in open_positions:
        print(
            f"         {p['symbol']} {p['signal']} "
            f"| SL={p.get('stop_loss')} TP={p.get('take_profit')} "
            f"| {p['order_id']}"
        )