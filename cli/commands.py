"""
TEDA CLI commands — each function implements one Alpaca CLI subcommand.

All commands use the shared BrokerClient + SMV strategy engine.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from execution.client import BrokerClient
from data.market_clock import is_market_open, next_open_str, closed_message
from data.market_data import fetch_stock_bars
from strategy import imbalance, liquidity, structure, supply_demand, triggers

WATCHLIST = ["SPY", "QQQ", "NVDA", "AAPL", "FXE", "FXB", "FXY", "GLD", "IWM", "MSFT"]
SIGNAL_FILE = Path(__file__).resolve().parent.parent / "logs" / "agent_stop.signal"


# ---- Account ----------------------------------------------------------------


def cmd_account() -> None:
    """Display Alpaca paper account summary."""
    broker = BrokerClient()
    acc = broker.get_account()
    initial = 100_000.0
    equity = float(acc.equity)
    pnl = equity - initial
    pnl_pct = (pnl / initial) * 100

    print("=" * 50)
    print("  📊 Compte Alpaca Paper")
    print("=" * 50)
    print(f"  Équité         : ${equity:,.2f}")
    print(f"  P&L            : ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
    print(f"  Cash           : ${float(acc.cash):,.2f}")
    print(f"  Buying Power   : ${float(acc.buying_power):,.2f}")
    print(f"  Portfolio      : ${float(acc.portfolio_value):,.2f}")
    print(f"  Statut         : {acc.status}")
    if acc.daytrade_count is not None:
        print(f"  Day trades     : {acc.daytrade_count}")
    print("=" * 50)


# ---- Positions --------------------------------------------------------------


def cmd_positions() -> None:
    """List open positions from Alpaca (not just tracked)."""
    broker = BrokerClient()
    positions = broker.trading.get_all_positions()

    if not positions:
        print("Aucune position ouverte.")
        return

    print(f"{'Symbole':12} {'Qté':>6} {'Mkt Value':>12} {'P&L Jour':>10} {'P&L Total':>10}")
    print("-" * 55)
    for p in positions:
        print(
            f"{p.symbol:12} {float(p.qty):>6.0f} "
            f"${float(p.market_value):>11,.2f} "
            f"${float(p.unrealized_intraday_pl or 0):>9,.2f} "
            f"${float(p.unrealized_pl or 0):>9,.2f}"
        )


# ---- Orders -----------------------------------------------------------------


def cmd_orders() -> None:
    """Show last 10 orders."""
    broker = BrokerClient()
    orders = list(broker.trading.get_orders())
    orders = orders[-10:]  # last 10

    if not orders:
        print("Aucun ordre récent.")
        return

    print(f"{'ID':38} {'Symbole':10} {'Side':6} {'Qty':>5} {'Statut':10} {'Soumis'}")
    print("-" * 80)
    for o in orders:
        created = str(o.created_at)[:19] if o.created_at else "?"
        print(
            f"{o.id:38} {o.symbol:10} {o.side.value:6} "
            f"{float(o.qty or 0):>5.0f} {o.status.value:10} {created}"
        )


# ---- Watchlist --------------------------------------------------------------


def cmd_watchlist() -> None:
    """Run the SMV analysis on all 10 watchlist assets and display results."""
    broker = BrokerClient()
    market_open = is_market_open()

    print("=" * 80)
    print(f"  🔭 Watchlist SMV — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    if not market_open:
        print(f"  ⚠️  Marché fermé — données figées sur la dernière clôture")
    print("=" * 80)
    print(f"{'Actif':6} {'Biais':8} {'Signal':12} {'Prix':>8} {'RR':>6} {'Filtres':30}")
    print("-" * 80)

    for sym in WATCHLIST:
        try:
            df_1d = fetch_stock_bars(broker.stock_data, sym, "1D", limit=200)
            df_1h = fetch_stock_bars(broker.stock_data, sym, "1H", limit=300)
        except Exception:
            print(f"  {sym:6} {'ERR':8} {'N/A':12} {'N/A':>8}")
            continue

        if df_1d.empty or df_1h.empty:
            print(f"  {sym:6} {'N/A':8} {'N/A':12} {'N/A':>8}")
            continue

        try:
            s = structure.analyze_structure(df_1d, lookback=5)
            zones = supply_demand.detect_zones(df_1h)
            supply_demand.mark_mitigated(df_1h, zones)
            breakers = supply_demand.detect_breaker_blocks(df_1h, zones)
            fvgs = imbalance.analyze_imbalance(df_1h)
            levels = liquidity.analyze_liquidity(df_1h, lookback=5)
            price = float(df_1h["close"].iloc[-1])

            # Try directional first, then consolidation
            # Try directional first, then consolidation fallback
            if s.bias in ("bullish", "bearish"):
                sig = triggers.evaluate_trigger(
                    structure_htf=s, zones=zones + breakers,
                    fvgs=fvgs, liquidity=levels, df_ltf=df_1h, current_price=price,
                )
                # If directional fails, try consolidation
                if sig.signal == "NONE":
                    condor = triggers.evaluate_consolidation(
                        zones=zones + breakers, fvgs=fvgs, liquidity=levels,
                        current_price=price,
                    )
                    if condor.signal == "IRON_CONDOR":
                        sig = condor
                        sig.bias = s.bias
            else:
                sig = triggers.evaluate_consolidation(
                    zones=zones + breakers, fvgs=fvgs, liquidity=levels,
                    current_price=price,
                )
                if sig.signal == "IRON_CONDOR":
                    sig.bias = s.bias
        except Exception as e:
            print(f"  {sym:6} {'ERR':8} {'ERR':12} error: {str(e)[:40]}")
            continue

        # Build filter status string
        filters = sig.filters_passed
        icons = []
        for fname in ["bias", "zone", "imbalance", "liquidity", "market_shift"]:
            icons.append("✅" if filters.get(fname) else "❌")
        filter_str = " ".join(icons)

        rr_str = f"{sig.rr_ratio:.1f}" if sig.rr_ratio else "—"

        print(
            f"  {sym:6} {s.bias:8} {sig.signal:12} "
            f"${price:>7.2f} {rr_str:>6} {filter_str:30}"
        )

    print("=" * 80)


# ---- Status -----------------------------------------------------------------


def cmd_status() -> None:
    """Market clock + quick account summary."""
    market_open = is_market_open()
    broker = BrokerClient()
    acc = broker.get_account()

    print("=" * 50)
    print("  📈 TEDA · Status")
    print("=" * 50)

    if market_open:
        print("  🟢 Marché US OUVERT")
        print(f"     Fermeture : 16h00 ET (20h00 Abidjan)")
    else:
        print("  🔴 Marché US FERMÉ")
        print(f"     Prochaine ouverture : {next_open_str()}")

    equity = float(acc.equity)
    initial = 100_000.0
    pnl = equity - initial
    pnl_pct = (pnl / initial) * 100
    print(f"\n  💰 Équité    : ${equity:,.2f}")
    print(f"  📊 P&L       : ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
    print(f"  💵 BP        : ${float(acc.buying_power):,.2f}")
    print("=" * 50)


# ---- Export -----------------------------------------------------------------


def cmd_export() -> None:
    """Export watchlist signals to CSV."""
    import csv
    from io import StringIO

    broker = BrokerClient()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Actif", "Signal", "Biais", "Prix", "Filtres", "RR", "SL", "TP", "Raison"])

    for sym in WATCHLIST:
        try:
            df_1d = fetch_stock_bars(broker.stock_data, sym, "1D", limit=200)
            df_1h = fetch_stock_bars(broker.stock_data, sym, "1H", limit=300)
        except Exception:
            writer.writerow([sym, "ERR", "?", "", "", "", "", "", "API error"])
            continue

        if df_1d.empty or df_1h.empty:
            writer.writerow([sym, "N/A", "?", "", "", "", "", "", "no data"])
            continue

        try:
            s = structure.analyze_structure(df_1d, lookback=5)
            zones = supply_demand.detect_zones(df_1h)
            supply_demand.mark_mitigated(df_1h, zones)
            breakers = supply_demand.detect_breaker_blocks(df_1h, zones)
            fvgs = imbalance.analyze_imbalance(df_1h)
            levels = liquidity.analyze_liquidity(df_1h, lookback=5)
            price = float(df_1h["close"].iloc[-1])

            if s.bias in ("bullish", "bearish"):
                sig = triggers.evaluate_trigger(
                    structure_htf=s, zones=zones + breakers,
                    fvgs=fvgs, liquidity=levels, df_ltf=df_1h, current_price=price,
                )
                if sig.signal == "NONE":
                    condor = triggers.evaluate_consolidation(
                        zones=zones + breakers, fvgs=fvgs, liquidity=levels,
                        current_price=price,
                    )
                    if condor.signal == "IRON_CONDOR":
                        sig = condor
                        sig.bias = s.bias
            else:
                sig = triggers.evaluate_consolidation(
                    zones=zones + breakers, fvgs=fvgs, liquidity=levels,
                    current_price=price,
                )
                if sig.signal == "IRON_CONDOR":
                    sig.bias = s.bias
        except Exception as e:
            writer.writerow([sym, "ERR", "?", "", "", "", "", "", str(e)[:60]])
            continue

        icons = " ".join("✅" if sig.filters_passed.get(f) else "❌" for f in
                         ["bias", "zone", "imbalance", "liquidity", "market_shift"])
        rr = f"{sig.rr_ratio:.1f}" if sig.rr_ratio else ""
        sl = f"{sig.stop_loss:.2f}" if sig.stop_loss else ""
        tp = f"{sig.take_profit:.2f}" if sig.take_profit else ""
        writer.writerow([sym, sig.signal, s.bias, f"{price:.2f}",
                         icons, rr, sl, tp, sig.reason])

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M")
    filename = f"{ts}_export.csv"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    print(f"✅ Exporté → {filename}")


# ---- Agent control ----------------------------------------------------------


def cmd_agent_start() -> None:
    """Start the autonomous agent loop (blocking)."""
    print("🚀 Démarrage de l'agent autonome SMV...")
    print(f"   Actifs : {', '.join(WATCHLIST)}")
    print(f"   Boucle : toutes les 5 minutes")
    print(f"   Arrêt  : Ctrl+C ou créer {SIGNAL_FILE}")
    print()

    from agent.main import _auto_loop
    _auto_loop(watchlist=WATCHLIST, live=True, use_llm=False, interval_min=5)


def cmd_agent_stop() -> None:
    """Create a stop signal file to gracefully stop a running agent."""
    SIGNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    SIGNAL_FILE.write_text("stop")
    print(f"🛑 Signal d'arrêt créé : {SIGNAL_FILE}")
    print("   L'agent s'arrêtera à la fin du cycle en cours.")


# ---- Manual trade -----------------------------------------------------------


def cmd_trade(symbol: str, action: str) -> None:
    """Execute a single manual trade via the CLI."""
    from agent.main import analyze_symbol, _place_paper_order
    from agent import risk

    broker = BrokerClient()

    if not is_market_open():
        print(closed_message())
        print("   ⚠️  Trade manuel impossible — marché fermé.")
        return

    print(f"📊 Analyse de {symbol}...")
    result = analyze_symbol(broker, symbol)
    if result is None:
        print(f"❌ Impossible d'analyser {symbol}")
        return

    signal, price = result
    if signal.signal == "NONE":
        print(f"❌ Aucun signal pour {symbol} — les filtres SMV ne sont pas alignés.")
        print(f"   Raison : {signal.reason}")
        return

    if signal.signal != action:
        print(f"⚠️  Signal SMV = {signal.signal}, action demandée = {action}")
        print(f"   L'agent suit toujours le signal SMV. Annulation.")
        return

    equity = broker.get_equity()
    risk_amount = risk.compute_risk_amount(equity)

    if signal.signal in ("BUY", "SELL") and not risk.check_rr_ratio(signal):
        print(f"❌ RR {signal.rr_ratio} < minimum {risk.settings.min_rr_ratio}")
        return

    print(f"✅ Signal {action} confirmé — placement de l'ordre...")
    _place_paper_order(broker, symbol, signal, risk_amount)
    print("✅ Trade exécuté.")


# ---- Daily Report ------------------------------------------------------------


def cmd_report() -> None:
    """Generate the daily trading report (market close summary)."""
    from agent.reporter import generate_daily_summary

    print("📝 Génération du rapport quotidien...")
    path = generate_daily_summary()
    if path:
        print(f"✅ Rapport sauvegardé : {path}")
        # Show it
        from pathlib import Path
        content = Path(path).read_text(encoding="utf-8")
        print("\n" + "=" * 60)
        print(content)
    else:
        print("⚠️  Impossible de générer le rapport.")