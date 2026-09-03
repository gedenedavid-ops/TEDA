"""
Dashboard Streamlit — Options Alpha Agent (SMV × Alpaca × Featherless)

Lancement :
    streamlit run dashboard.py

Ou avec port personnalisé :
    streamlit run dashboard.py --server.port 8502
"""

from __future__ import annotations

import json
import sys
import threading
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

# Page config — must be the first st call.
st.set_page_config(
    page_title="Options Alpha Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- CSS minimal (dark theme friendly) -----------------------------------
st.markdown(
    """
<style>
    .signal-buy  { color: #00ff88; font-weight: bold; }
    .signal-sell { color: #ff4444; font-weight: bold; }
    .signal-condor { color: #ffaa00; font-weight: bold; }
    .signal-none { color: #888888; }
    .metric-positive { color: #00ff88; }
    .metric-negative { color: #ff4444; }
    .stApp { margin-top: -30px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---- Agent background worker --------------------------------------------


def _agent_worker(live: bool = True) -> None:
    """Background thread: runs the agent loop continuously."""
    import sys
    from agent.main import run as agent_run
    from data.market_clock import is_market_open, closed_message

    cycle = 0
    while st.session_state.get("agent_running", False):
        cycle += 1
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        header = f"\n=== Cycle #{cycle} — {ts} ===\n"

        try:
            # Capture stdout to log file
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            if is_market_open():
                agent_run(
                    watchlist=["SPY", "QQQ", "NVDA", "AAPL", "FXE", "FXB", "FXY", "GLD", "IWM", "MSFT"],
                    live=live,
                    use_llm=False,
                )
            else:
                print(closed_message())

            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

            # Also print to real stdout for terminal
            print(header + output, flush=True)

            # Append to log file
            with open(AGENT_LOG, "a", encoding="utf-8") as f:
                f.write(header + output)

            st.session_state.agent_last_cycle = cycle
            st.session_state.agent_last_ts = ts
        except Exception as exc:
            print(f"[ERREUR AGENT] {exc}", flush=True)

        # Wait 5 minutes between cycles
        for _ in range(300):  # 5 minutes = 300 seconds
            if not st.session_state.get("agent_running", False):
                break
            time.sleep(1)


def start_agent() -> None:
    """Start the agent in a background thread."""
    if st.session_state.get("agent_running", False):
        return
    st.session_state.agent_running = True
    st.session_state.agent_started_at = datetime.now(timezone.utc).strftime("%H:%M UTC")
    st.session_state.agent_last_cycle = 0
    thread = threading.Thread(target=_agent_worker, args=(True,), daemon=True)
    thread.start()
    st.session_state.agent_thread = thread


def stop_agent() -> None:
    """Stop the background agent."""
    st.session_state.agent_running = False
    st.session_state.agent_last_cycle = 0


# ---- Paths ---------------------------------------------------------------
LOGS_DIR = Path(__file__).resolve().parent / "logs"
TRADE_LOG = LOGS_DIR / "trades.md"
POSITIONS_FILE = LOGS_DIR / "positions.json"
AGENT_LOG = LOGS_DIR / "agent_output.txt"


# ---- Data helpers ---------------------------------------------------------


@st.cache_data(ttl=30)
def fetch_market_status() -> Dict[str, Any]:
    """Market open/close + next open (cached 30s)."""
    from data.market_clock import is_market_open, next_open_str

    return {
        "open": is_market_open(),
        "next": next_open_str(),
    }


@st.cache_data(ttl=60)
def fetch_account() -> Dict[str, Any]:
    """Account equity, cash, buying power (cached 60s)."""
    from execution.client import BrokerClient

    try:
        broker = BrokerClient()
        acc = broker.get_account()
        return {
            "equity": float(acc.equity),
            "cash": float(acc.cash),
            "buying_power": float(acc.buying_power),
            "portfolio_value": float(acc.portfolio_value),
            "initial": 100_000.0,
        }
    except Exception:
        return {"equity": 100_000, "cash": 100_000, "buying_power": 200_000, "portfolio_value": 0, "initial": 100_000}


@st.cache_data(ttl=120)
def fetch_watchlist_signals(symbols: List[str]) -> List[Dict[str, Any]]:
    """Run the SMV chain on all symbols, return signal summary (cached 2 min)."""
    from execution.client import BrokerClient
    from data.market_data import fetch_stock_bars
    from strategy import imbalance, liquidity, structure, supply_demand, triggers

    results = []
    try:
        broker = BrokerClient()
    except Exception as e:
        return [{"symbol": s, "signal": "ERR", "bias": "?", "price": 0, "rr": None, "reason": str(e)} for s in symbols]

    for sym in symbols:
        try:
            df_1d = fetch_stock_bars(broker.stock_data, sym, "1D", limit=200)
            df_1h = fetch_stock_bars(broker.stock_data, sym, "1H", limit=300)
        except Exception as e:
            results.append({"symbol": sym, "signal": "ERR", "bias": "?", "price": 0, "rr": None, "filters": {}, "reason": f"API: {e}"})
            continue

        if df_1d.empty or df_1h.empty:
            results.append({"symbol": sym, "signal": "N/A", "bias": "?", "price": 0, "rr": None, "filters": {}, "reason": "no data"})
            continue

        try:
            s = structure.analyze_structure(df_1d, lookback=5)
            zones = supply_demand.detect_zones(df_1h)
            supply_demand.mark_mitigated(df_1h, zones)
            breakers = supply_demand.detect_breaker_blocks(df_1h, zones)
            fvgs = imbalance.analyze_imbalance(df_1h)
            levels = liquidity.analyze_liquidity(df_1h, lookback=5)
            price = float(df_1h["close"].iloc[-1])

            # Try directional first, then consolidation fallback
            if s.bias in ("bullish", "bearish"):
                signal = triggers.evaluate_trigger(
                    structure_htf=s, zones=zones + breakers, fvgs=fvgs,
                    liquidity=levels, df_ltf=df_1h, current_price=price,
                )
                # If directional fails, try consolidation
                if signal.signal == "NONE":
                    condor = triggers.evaluate_consolidation(
                        zones=zones + breakers, fvgs=fvgs, liquidity=levels,
                        current_price=price,
                    )
                    if condor.signal == "IRON_CONDOR":
                        signal = condor
                        signal.bias = s.bias
            else:
                signal = triggers.evaluate_consolidation(
                    zones=zones + breakers, fvgs=fvgs, liquidity=levels,
                    current_price=price,
                )
                if signal.signal == "IRON_CONDOR":
                    signal.bias = s.bias
        except Exception as e:
            results.append({"symbol": sym, "signal": "ERR", "bias": "?", "price": 0, "rr": None, "filters": {}, "reason": str(e)})
            continue

        # Format filter status for display
        filter_icons = {}
        for fname, passed in signal.filters_passed.items():
            filter_icons[fname] = "✅" if passed else "❌"

        # Reason display
        if signal.signal == "NONE":
            reason_display = signal.reason
        elif signal.signal == "IRON_CONDOR":
            reason_display = signal.reason
        else:
            reason_display = "5/5 filtres ✅"

        # Entry display
        if signal.signal == "IRON_CONDOR":
            entry_display = f"{signal.support:.1f}–{signal.resistance:.1f}"
        elif signal.signal != "NONE":
            entry_display = f"{signal.entry_bottom:.1f}-{signal.entry_top:.1f}"
        else:
            entry_display = ""

        results.append({
            "symbol": sym,
            "signal": signal.signal,
            "bias": s.bias,
            "price": round(price, 2),
            "rr": round(signal.rr_ratio, 1) if signal.rr_ratio else None,
            "filters": filter_icons,
            "reason": reason_display,
            "entry": entry_display,
            "sl": round(signal.stop_loss, 2) if signal.stop_loss else None,
            "tp": round(signal.take_profit, 2) if signal.take_profit else None,
        })

    return results


def load_positions() -> List[Dict[str, Any]]:
    """Open tracked positions."""
    if not POSITIONS_FILE.exists():
        return []
    with open(POSITIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_trade_log(n: int = 20) -> str:
    """Last N trades from the markdown journal."""
    if not TRADE_LOG.exists():
        return "*Aucun trade pour le moment.*"
    with open(TRADE_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    buf: List[str] = []
    for line in lines:
        if line.startswith("## "):
            if buf:
                entries.append("".join(buf))
            buf = [line]
        elif buf:
            buf.append(line)
    if buf:
        entries.append("".join(buf))

    return "\n".join(entries[-n:])


# ---- UI Components --------------------------------------------------------


def render_sidebar() -> None:
    """Sidebar: account + market status + controls."""
    with st.sidebar:
        st.title("📊 Options Alpha Agent")
        st.caption("SMV × Alpaca × Featherless")

        st.divider()

        # Market status
        market = fetch_market_status()
        if market["open"]:
            st.success("🟢 **Marché US ouvert**")
        else:
            st.error(f"🔴 **Marché US fermé**\n\nProchaine ouverture : {market['next']}")

        st.divider()

        # Account
        acc = fetch_account()
        pnl = acc["equity"] - acc["initial"]
        pnl_pct = (pnl / acc["initial"]) * 100

        col1, col2 = st.columns(2)
        col1.metric("Équité", f"${acc['equity']:,.0f}")
        col2.metric(
            "P&L",
            f"${pnl:+,.0f}",
            f"{pnl_pct:+.2f}%",
        )
        st.metric("Buying Power", f"${acc['buying_power']:,.0f}")

        st.divider()

        # Positions ouvertes
        positions = load_positions()
        open_pos = [p for p in positions if not p.get("closed")]
        st.metric("Positions ouvertes", len(open_pos))

        if open_pos:
            for p in open_pos:
                st.caption(
                    f"{p['signal']} **{p['symbol']}** | "
                    f"SL ${p.get('stop_loss', '?')} | TP ${p.get('take_profit', '?')}"
                )

        st.divider()

        # Agent controls
        st.subheader("🤖 Agent Trading")

        agent_running = st.session_state.get("agent_running", False)

        if agent_running:
            st.success(f"🟢 Agent actif — cycle {st.session_state.get('agent_last_cycle', 0)}")
            st.caption(f"Démarré : {st.session_state.get('agent_started_at', '?')}")
            if st.button("⏹️ Arrêter l'agent", type="primary", use_container_width=True):
                stop_agent()
                st.rerun()
        else:
            st.warning("⚪ Agent arrêté")
            if st.button("▶️ Lancer l'agent", type="primary", use_container_width=True):
                start_agent()
                st.rerun()

        st.divider()

        # Quick commands
        st.caption("**Commandes terminal :")
        st.code("python -m agent.main --live --loop 5 --no-llm", language="bash")
        st.code("streamlit run dashboard.py", language="bash")


def render_watchlist() -> None:
    """Main panel: watchlist table with signals."""
    st.header("🔭 Watchlist — Signaux SMV")

    # Banner if market closed
    market = fetch_market_status()
    if not market["open"]:
        st.warning("🔴 Marché US fermé — données figées sur la dernière clôture. Aucun ordre live possible.")

    with st.spinner("Analyse des 10 actifs..."):
        signals = fetch_watchlist_signals([
            "SPY", "QQQ", "NVDA", "AAPL",
            "FXE", "FXB", "FXY", "GLD", "IWM", "MSFT",
        ])

    if not signals:
        st.error("Impossible de récupérer les données. Vérifie la connexion Alpaca.")
        return

    # Build compact table
    rows = []
    for s in signals:
        sig = s["signal"]
        if sig == "BUY":
            sig_display = "🟢 BUY"
        elif sig == "SELL":
            sig_display = "🔴 SELL"
        elif sig == "IRON_CONDOR":
            sig_display = "🟡 IRON CONDOR"
        elif sig in ("ERR", "N/A"):
            sig_display = f"⚠️ {sig}"
        else:
            sig_display = "⚪"

        # Filter icons string
        f = s.get("filters", {})
        filters_str = " ".join(f.values()) if f else ""

        rows.append({
            "Actif": s["symbol"],
            "Signal": sig_display,
            "Biais": s["bias"][:4].upper(),
            "Prix": f"{s['price']:.2f}",
            "Filtres": filters_str,
            "RR": f"{s['rr']:.1f}" if s["rr"] else "",
            "SL": f"{s['sl']:.2f}" if s.get("sl") else "",
            "TP": f"{s['tp']:.2f}" if s.get("tp") else "",
            "Raison": s["reason"][:80],
        })

    df = pd.DataFrame(rows)

    def color_signal(val: str) -> str:
        if "BUY" in val:
            return "background-color: #004d26; color: #00ff88; font-weight: bold"
        if "SELL" in val:
            return "background-color: #4d0000; color: #ff4444; font-weight: bold"
        if "CONDOR" in val:
            return "background-color: #4d3300; color: #ffaa00; font-weight: bold"
        return ""

    styled = df.style.map(color_signal, subset=["Signal"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

    # Counts
    buy_count = sum(1 for s in signals if s["signal"] == "BUY")
    sell_count = sum(1 for s in signals if s["signal"] == "SELL")
    condor_count = sum(1 for s in signals if s["signal"] == "IRON_CONDOR")
    none_count = sum(1 for s in signals if s["signal"] == "NONE")

    cols = st.columns(5)
    cols[0].metric("🟢 BUY", buy_count)
    cols[1].metric("🔴 SELL", sell_count)
    cols[2].metric("🟡 IRON", condor_count)
    cols[3].metric("⚪ NONE", none_count)
    cols[4].metric("Total", len(signals))

    # Filter legend
    with st.expander("📊 Légende des filtres"):
        st.caption("✅ = OK | ❌ = manquant | Colonnes : Biais / Zone OB / FVG / Liquidité / Market Shift")
        st.caption("Les signaux NONE sont normaux : l'agent attend l'alignement parfait des 5 filtres SMV.")

    # Show active signal details
    active = [s for s in signals if s["signal"] in ("BUY", "SELL", "IRON_CONDOR")]
    if active:
        st.divider()
        st.subheader("🎯 Signaux actifs")
        for s in active:
            if s["signal"] == "IRON_CONDOR":
                st.warning(
                    f"**{s['symbol']}** — {s['signal']} | "
                    f"Range {s.get('entry', '?')} | Raison : {s.get('reason', '?')[:60]}"
                )
            else:
                st.success(
                    f"**{s['symbol']}** — {s['signal']} | "
                    f"Entrée {s.get('entry', '?')} | SL ${s.get('sl', '?')} | TP ${s.get('tp', '?')} | RR {s.get('rr', '?')}"
                )
    else:
        st.info("Aucun signal actif pour le moment. L'agent attend l'alignement des 5 filtres SMV.")


def render_positions() -> None:
    """Open positions panel."""
    st.header("📌 Positions ouvertes")

    positions = load_positions()
    open_pos = [p for p in positions if not p.get("closed")]
    closed_pos = [p for p in positions if p.get("closed")]

    if not positions:
        st.info("Aucune position trackée. L'agent n'a pas encore placé de trade.")
        return

    # Open
    if open_pos:
        st.subheader(f"🟢 Ouvertes ({len(open_pos)})")
        for p in open_pos:
            with st.container(border=True):
                cols = st.columns(4)
                cols[0].metric("Actif", p["symbol"])
                cols[1].metric("Signal", p["signal"])
                cols[2].metric("SL", f"${p.get('stop_loss', '?')}")
                cols[3].metric("TP", f"${p.get('take_profit', '?')}")
                st.caption(f"Ordre: `{p['order_id']}` | Ouvert: {p.get('opened_at', '?')}")

    # Closed
    if closed_pos:
        st.divider()
        st.subheader(f"🔴 Fermées ({len(closed_pos)})")
        for p in closed_pos[-10:]:
            with st.container(border=True):
                cols = st.columns(5)
                cols[0].metric("Actif", p["symbol"])
                cols[1].metric("Signal", p["signal"])
                reason = p.get("close_reason", "?")
                cols[2].metric("Sortie", reason)
                cols[3].metric("Prix sortie", f"${p.get('close_price', '?')}")
                cols[4].metric("Fermé", str(p.get("closed_at", "?"))[:19])


def render_history() -> None:
    """Trade history panel."""
    st.header("📜 Historique des trades")

    log_content = load_trade_log(30)
    if log_content.startswith("*Aucun"):
        st.info(log_content)
    else:
        st.markdown(log_content)

    st.caption(f"Journal complet : `{TRADE_LOG}`")


def render_strategy() -> None:
    """Quick reference: SMV 5-filter chain."""
    st.header("📖 Stratégie SMV — Les 5 filtres")

    filters = [
        ("1️⃣ Biais HTF", "Structure D1 : HH+HL (bullish) ou LH+LL (bearish). Règle 80/20."),
        ("2️⃣ Zone OB", "Zone d'offre/demande non mitigée sur H1. Origine : manipulative, money take, breaker."),
        ("3️⃣ Imbalance (FVG)", "Fair Value Gap qui confirme la zone. L'imbalance n'est pas un signal isolé."),
        ("4️⃣ Liquidité sweepée", "Liquidité externe DÉJÀ nettoyée = zone prioritaire. Sinon = inducement (piège)."),
        ("5️⃣ Market Shift LTF", "Changement de caractère sur le LTF : clôture au-delà du dernier BOS."),
    ]

    for title, desc in filters:
        with st.expander(title):
            st.write(desc)

    st.divider()
    st.subheader("🎯 Stratégies Options (B/B/B)")
    st.markdown("""
    - **BUY** → **Call Debit Spread** (achat call + vente call plus haut)
    - **SELL** → **Put Debit Spread** (achat put + vente put plus bas)
    - **Consolidation** → **Iron Condor** (vente put spread + vente call spread) ✅ actif
    """)

    st.caption("Risque 1% / trade | RR minimum 1:7 | Sortie auto SL/TP")


# ---- Main -----------------------------------------------------------------


def main() -> None:
    st.title("🤖 Options Alpha Agent")
    st.caption("Agent de trading autonome — Hackathon lablab.ai × Alpaca • Septembre 2026")

    # Sidebar
    render_sidebar()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔭 Watchlist", "📌 Positions", "📜 Historique", "📖 Stratégie"
    ])

    with tab1:
        render_watchlist()

    with tab2:
        render_positions()

    with tab3:
        render_history()

    with tab4:
        render_strategy()

    # Footer
    st.divider()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.caption(
        f"🔄 Rafraîchissement auto toutes les 60s | Dernière mise à jour : {ts} | "
        "Compte Alpaca Paper • $100,000"
    )

    # Auto-refresh
    time.sleep(60)
    st.rerun()


if __name__ == "__main__":
    main()