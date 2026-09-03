"""
Autonomous agent loop.

For each symbol in the watchlist:
  1. Fetch HTF (1D) and LTF (1H) bars from Alpaca.
  2. Run the SMV 5-filter chain.
  3. If a BUY/SELL signal is emitted, validate risk (1%, 1:7), journal the
     decision (optionally with LLM reasoning), and place a paper order.

Usage:
    python -m agent.main                  # dry-run (journal only, no orders)
    python -m agent.main --live           # place real paper orders
"""

from __future__ import annotations

import argparse
from typing import List, Optional

from agent import decision, risk
from data.market_clock import closed_message, is_market_open
from data.market_data import fetch_stock_bars
from execution.client import BrokerClient
from strategy import imbalance, liquidity, structure, supply_demand, triggers
from strategy.models import Signal

# Watchlist of liquid underlyings with active options chains.
# 10 assets: stocks/ETFs + forex via ETFs (pending trader confirmation).
WATCHLIST = ["SPY", "QQQ", "NVDA", "AAPL", "FXE", "FXB", "FXY", "GLD", "IWM", "MSFT"]


def analyze_symbol(broker: BrokerClient, symbol: str) -> Optional[tuple[Signal, float]]:
    """Run the full SMV chain for one symbol. Returns (signal, price)."""
    df_1d = fetch_stock_bars(broker.stock_data, symbol, "1D", limit=400)
    df_1h = fetch_stock_bars(broker.stock_data, symbol, "1H", limit=500)

    if df_1d.empty or df_1h.empty:
        print(f"  [{symbol}] pas de données (skip)")
        return None

    s = structure.analyze_structure(df_1d, lookback=5)
    zones = supply_demand.detect_zones(df_1h)
    supply_demand.mark_mitigated(df_1h, zones)
    breakers = supply_demand.detect_breaker_blocks(df_1h, zones)
    fvgs = imbalance.analyze_imbalance(df_1h)
    levels = liquidity.analyze_liquidity(df_1h, lookback=5)

    current_price = float(df_1h["close"].iloc[-1])

    # Step 1: Try directional trigger (BUY / SELL)
    if s.bias in ("bullish", "bearish"):
        signal = triggers.evaluate_trigger(
            structure_htf=s,
            zones=zones + breakers,
            fvgs=fvgs,
            liquidity=levels,
            df_ltf=df_1h,
            current_price=current_price,
        )
    else:
        signal = Signal(signal="NONE", bias=s.bias, reason="No clear HTF bias (consolidation)")

    # Step 2: If no directional signal, try consolidation (Iron Condor)
    if signal.signal == "NONE":
        condor = triggers.evaluate_consolidation(
            zones=zones + breakers,
            fvgs=fvgs,
            liquidity=levels,
            current_price=current_price,
        )
        if condor.signal == "IRON_CONDOR":
            signal = condor
            # Inherit bias from structure
            signal.bias = s.bias

    print(
        f"  [{symbol}] biais={s.bias:8s} signal={signal.signal:4s} "
        f"@ {current_price:.2f}"
    )
    if signal.signal != "NONE":
        print(f"           -> {signal.reason}")
        if signal.signal in ("BUY", "SELL"):
            print(
                f"           entrée {signal.entry_bottom:.2f}-{signal.entry_top:.2f} "
                f"| SL {signal.stop_loss:.2f} | TP {signal.take_profit:.2f} | RR {signal.rr_ratio}"
            )
        elif signal.signal == "IRON_CONDOR":
            print(
                f"           range {signal.support:.2f}-{signal.resistance:.2f} "
                f"| support={signal.entry_bottom:.2f} resistance={signal.entry_top:.2f}"
            )

    return signal, current_price


def run(watchlist: List[str], live: bool = False, use_llm: bool = True) -> None:
    market_open = is_market_open()

    if not market_open:
        print(closed_message())
        if live:
            return  # jamais d'ordres live marché fermé
        print("  (dry-run autorisé — données figées sur la dernière clôture)\n")

    broker = BrokerClient()

    # ---- Exit monitor: close positions at SL / TP first -------------------
    from agent.exit import check_and_exit, print_summary

    print_summary()
    if live:
        closed = check_and_exit(broker)
        if closed > 0:
            print(f"  [exit] {closed} position(s) fermée(s) sur SL/TP\n")

    equity = broker.get_equity()

    for symbol in watchlist:
        print(f"\nAnalyse de {symbol} ...")
        result = analyze_symbol(broker, symbol)

        if result is None:
            continue
        signal, current_price = result
        if signal.signal == "NONE":
            continue

        # ---- Risk gate (directional only) -------------------------------
        if signal.signal in ("BUY", "SELL"):
            if not risk.check_rr_ratio(signal):
                print(f"  -> rejeté : RR {signal.rr_ratio} < minimum {risk.settings.min_rr_ratio}")
                decision.log_decision(
                    signal, symbol, current_price, action="REJETÉ (RR insuffisant)"
                )
                continue

        risk_amount = risk.compute_risk_amount(equity)
        reasoning = decision.reason_about_signal(signal, symbol, current_price) if use_llm else ""

        action = "PAPER ORDER (dry-run)" if not live else "PAPER ORDER (live)"
        decision.log_decision(signal, symbol, current_price, action, reasoning)

        if live:
            # Prevent duplicate orders: skip if already have open position on this symbol
            from agent.exit import has_open_position

            if has_open_position(symbol):
                print(f"  -> déjà une position ouverte sur {symbol}, skip")
                continue

            print(f"  -> {action} | risque max ${risk_amount:.2f} | {reasoning}")
            _place_paper_order(broker, symbol, signal, risk_amount)
        else:
            print(f"  -> {action} | risque max ${risk_amount:.2f} | {reasoning}")


def _place_paper_order(
    broker: BrokerClient, symbol: str, signal: Signal, risk_amount: float
) -> None:
    """Build and place a multi-leg options order based on the SMV signal.

    BUY  -> Call Debit Spread  (BTO call + STO higher call)
    SELL -> Put Debit Spread   (BTO put  + STO lower put)
    IRON_CONDOR -> Iron Condor (STO put spread + STO call spread)
    """
    from execution import options
    from agent.exit import track_position

    order_req = None

    if signal.signal in ("BUY", "SELL"):
        order_req = options.build_debit_spread(broker, symbol, signal, risk_amount)
    elif signal.signal == "IRON_CONDOR":
        if signal.support is None or signal.resistance is None:
            print(f"  -> Iron Condor impossible : support/résistance manquants")
            return
        # Use current price from the entry zone midpoint
        current = (signal.entry_top + signal.entry_bottom) / 2
        order_req = options.build_iron_condor(
            broker, symbol, current, signal.support, signal.resistance, risk_amount
        )

    if order_req is None:
        print(f"  -> impossible de construire le spread pour {symbol}")
        return

    result = broker.submit_order(order_req)
    leg_symbols = [leg.symbol for leg in order_req.legs]
    spread_type = "Iron Condor" if signal.signal == "IRON_CONDOR" else "debit spread"
    print(f"  -> {spread_type} soumis : {result.id} | {len(leg_symbols)} jambes")
    for ls in leg_symbols:
        print(f"       {ls}")

    # Track for auto exit (SL / TP monitoring).
    # Iron condors don't use SL/TP the same way — they're managed by expiry.
    track_position(
        order_id=str(result.id),
        symbol=symbol,
        signal_str=signal.signal,
        stop_loss=signal.stop_loss if signal.signal != "IRON_CONDOR" else None,
        take_profit=signal.take_profit if signal.signal != "IRON_CONDOR" else None,
        leg_symbols=leg_symbols,
    )


def _auto_loop(
    watchlist: List[str],
    live: bool = False,
    use_llm: bool = True,
    interval_min: int = 10,
) -> None:
    """Run the agent continuously every `interval_min` minutes."""
    import json
    import os
    import time
    from datetime import datetime, timezone
    from pathlib import Path

    print(f"=== Agent SMV — boucle auto toutes les {interval_min} min ===")
    print(f"    Live: {live} | LLM: {use_llm} | Actifs: {len(watchlist)}")
    print(f"    Ctrl+C pour arrêter\n")

    # Status file for dashboard
    status_file = Path(__file__).resolve().parent.parent / "logs" / "agent_status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)

    def _write_status(cycle: int, ts: str) -> None:
        try:
            with open(status_file, "w") as f:
                json.dump({
                    "running": True,
                    "pid": os.getpid(),
                    "last_cycle": cycle,
                    "last_ts": ts,
                }, f)
        except Exception:
            pass  # never crash on status write

    iteration = 0
    while True:
        iteration += 1
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        print(f"\n{'='*60}")
        print(f"  Cycle #{iteration} — {ts}")
        print(f"{'='*60}")

        try:
            run(watchlist=watchlist, live=live, use_llm=use_llm)
        except Exception as exc:
            print(f"  [ERREUR] cycle {iteration}: {exc}")

        _write_status(iteration, ts)
        print(f"\n  Prochain cycle dans {interval_min} min...")
        time.sleep(interval_min * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SMV options alpha agent")
    parser.add_argument(
        "--live", action="store_true", help="placer de vrais ordres paper"
    )
    parser.add_argument(
        "--no-llm", action="store_true", help="désactiver le raisonnement LLM"
    )
    parser.add_argument(
        "--symbols", nargs="*", default=WATCHLIST, help="liste de sous-jacents"
    )
    parser.add_argument(
        "--loop", type=int, default=0, metavar="MINUTES",
        help="boucle automatique toutes les N minutes (0 = une seule passe)"
    )
    args = parser.parse_args()

    if args.loop > 0:
        _auto_loop(watchlist=args.symbols, live=args.live,
                   use_llm=not args.no_llm, interval_min=args.loop)
    else:
        run(watchlist=args.symbols, live=args.live, use_llm=not args.no_llm)
