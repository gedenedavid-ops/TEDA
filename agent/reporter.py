"""
Daily reporter: generates a trader-style summary at market close.

At the end of each trading day, the reporter:
  1. Collects all trades opened/closed today from the journal + positions log
  2. Fetches current account state (equity, P&L, positions)
  3. Sends structured data to the Featherless LLM for analysis
  4. Saves a human-readable summary to logs/daily_summary_YYYY-MM-DD.md

The LLM is prompted to act as a trader-secretary: factual, critical,
identifying what worked, what didn't, and what deserves attention tomorrow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
TRADE_LOG = LOGS_DIR / "trades.md"
POSITIONS_FILE = LOGS_DIR / "positions.json"


def _collect_todays_trades() -> List[str]:
    """Parse the trade journal and return entries for today only."""
    if not TRADE_LOG.exists():
        return []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries: List[str] = []
    current_entry: List[str] = []
    in_entry = False

    for line in TRADE_LOG.read_text(encoding="utf-8").split("\n"):
        if line.startswith("## ") and today in line:
            if current_entry:
                entries.append("\n".join(current_entry))
            current_entry = [line]
            in_entry = True
        elif in_entry:
            if line.startswith("## "):
                # New day → stop collecting
                if current_entry:
                    entries.append("\n".join(current_entry))
                in_entry = False
                current_entry = []
            else:
                current_entry.append(line)

    if current_entry:
        entries.append("\n".join(current_entry))

    return entries


def _collect_positions_state() -> str:
    """Read current tracked positions and return a summary string."""
    import json

    if not POSITIONS_FILE.exists():
        return "No tracked positions."

    try:
        data = json.loads(POSITIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "Unable to read positions file."

    open_pos = [p for p in data if p.get("status") == "open"]
    closed_pos = [p for p in data if p.get("status") != "open"]

    lines = []
    if open_pos:
        lines.append("**Positions ouvertes:**")
        for p in open_pos:
            lines.append(
                f"- {p.get('symbol')} {p.get('signal')} | "
                f"SL={p.get('stop_loss')} TP={p.get('take_profit')} | "
                f"order={str(p.get('order_id', '?'))[:8]}..."
            )
    if closed_pos:
        lines.append("**Positions fermées aujourd'hui:**")
        for p in closed_pos:
            reason = p.get('exit_reason', p.get('status', 'closed'))
            closed_ts = p.get('closed_at', '')
            if closed_ts:
                reason += f" @ {str(closed_ts)[:19]}"
            lines.append(
                f"- {p.get('symbol')} {p.get('signal')} | {reason}"
            )

    if not lines:
        return "No positions tracked today."
    return "\n".join(lines)


def _collect_watchlist_snapshot() -> str:
    """Run a quick SMV scan and return the watchlist state as text."""
    try:
        from execution.client import BrokerClient
        from data.market_data import fetch_stock_bars
        from strategy import imbalance, liquidity, structure, supply_demand, triggers

        broker = BrokerClient()
        symbols = ["SPY", "QQQ", "NVDA", "AAPL", "FXE", "FXB", "FXY", "GLD", "IWM", "MSFT"]
        lines = []

        for sym in symbols:
            try:
                df_1d = fetch_stock_bars(broker.stock_data, sym, "1D", limit=200)
                df_1h = fetch_stock_bars(broker.stock_data, sym, "1H", limit=300)
            except Exception:
                lines.append(f"- {sym}: data unavailable")
                continue

            if df_1d.empty or df_1h.empty:
                lines.append(f"- {sym}: no data")
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
                        fvgs=fvgs, liquidity=levels, df_ltf=df_1h,
                        current_price=price,
                    )
                    if sig.signal == "NONE":
                        condor = triggers.evaluate_consolidation(
                            zones=zones + breakers, fvgs=fvgs,
                            liquidity=levels, current_price=price,
                        )
                        if condor.signal == "IRON_CONDOR":
                            sig = condor
                else:
                    sig = triggers.evaluate_consolidation(
                        zones=zones + breakers, fvgs=fvgs,
                        liquidity=levels, current_price=price,
                    )

                filters_str = " ".join(
                    "✅" if sig.filters_passed.get(f) else "❌"
                    for f in ["bias", "zone", "imbalance", "liquidity", "market_shift"]
                )
                lines.append(
                    f"- {sym}: {sig.signal} @ ${price:.2f} | bias={s.bias} | "
                    f"filters=[{filters_str}] | {sig.reason[:80]}"
                )
            except Exception as e:
                lines.append(f"- {sym}: error ({str(e)[:50]})")

        return "\n".join(lines)
    except Exception as e:
        return f"Watchlist snapshot unavailable: {e}"


def _get_llm_client():
    """Return an OpenAI-compatible client for Featherless, or None."""
    from config.settings import settings

    if not settings.featherless_configured:
        return None

    from openai import OpenAI

    return OpenAI(
        api_key=settings.featherless_api_key,
        base_url=settings.featherless_base_url,
    )


def generate_daily_summary(account_summary: str = "") -> str:
    """Generate a trader-style daily summary and save to disk.

    Returns the path to the generated file, or an empty string on failure.
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = LOGS_DIR / f"daily_summary_{today_str}.md"

    # Don't regenerate if already exists
    if output_file.exists():
        return str(output_file)

    # Collect data
    trades = _collect_todays_trades()
    positions = _collect_positions_state()
    watchlist = _collect_watchlist_snapshot()

    trades_text = "\n\n".join(trades) if trades else "No trades executed today."
    if not account_summary:
        account_summary = "Account data unavailable."

    # Build prompt
    prompt = (
        "You are a professional trading desk secretary and Smart Money analyst. "
        "Write a concise daily recap (in French) for the trader. Structure:\n\n"
        "## 📊 Résumé du jour\n"
        "- Nombre de trades, P&L, équité.\n\n"
        "## 🔍 Analyse par trade\n"
        "- Pour chaque trade : ce qui a fonctionné ou pas, pourquoi.\n"
        "- Signaux NONE importants (setup presque complet).\n\n"
        "## ⚠️ Points d'attention\n"
        "- Trades qui méritent surveillance demain.\n"
        "- Filtres qui bloquent systématiquement.\n"
        "- Anomalies (sizing, slippage, time decay).\n\n"
        "## 💡 Recommandations pour demain\n"
        "- Actifs à surveiller en priorité.\n"
        "- Ajustements suggérés (SL, TP, sizing).\n\n"
        "Reste factuel, critique si nécessaire, pas de conseil financier.\n\n"
        "--- DATA ---\n"
        f"Compte: {account_summary}\n\n"
        f"Trades du jour:\n{trades_text}\n\n"
        f"Positions:\n{positions}\n\n"
        f"Watchlist (signaux de clôture):\n{watchlist}\n"
    )

    client = _get_llm_client()
    if client is None:
        # Fallback: generate a basic summary without LLM
        summary = _fallback_summary(trades, positions, watchlist, account_summary, today_str)
    else:
        from config.settings import settings

        try:
            resp = client.chat.completions.create(
                model=settings.featherless_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un secrétaire de trading desk. Tu analyses "
                            "la journée de trading avec un œil critique et "
                            "constructif. Tu identifies ce qui a marché, ce "
                            "qui n'a pas marché, et tu donnes des "
                            "recommandations pour le lendemain. Style : "
                            "professionnel, concis, en français."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1200,
            )
            if resp and resp.choices and len(resp.choices) > 0:
                choice = resp.choices[0]
                if choice.message and choice.message.content:
                    summary = choice.message.content.strip()
                else:
                    raise ValueError("LLM response has empty message content")
            else:
                raise ValueError("LLM response has no choices")
        except Exception as exc:
            summary = _fallback_summary(trades, positions, watchlist, account_summary, today_str)
            summary += f"\n\n*Note: LLM unavailable ({exc}), fallback summary generated.*"

    # Write to file
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    header = f"# TEDA — Rapport quotidien\n**Date** : {today_str}\n**Généré** : {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n\n---\n\n"
    output_file.write_text(header + summary, encoding="utf-8")

    return str(output_file)


def _fallback_summary(
    trades: List[str],
    positions: str,
    watchlist: str,
    account: str,
    today: str,
) -> str:
    """Generate a basic summary without LLM."""
    n_trades = len(trades)
    lines = [
        "## 📊 Résumé du jour",
        f"- Trades exécutés : {n_trades}",
        f"- Compte : {account}",
        "",
        "## 🔍 Trades du jour",
    ]
    if trades:
        for t in trades:
            lines.append(t)
            lines.append("")
    else:
        lines.append("Aucun trade aujourd'hui.")
        lines.append("")

    lines.extend([
        "## ⚠️ Points d'attention",
        positions,
        "",
        "## 💡 Watchlist (signaux de clôture)",
        watchlist,
        "",
        "*Rapport généré sans LLM (mode fallback).*",
    ])
    return "\n".join(lines)


def latest_summary_content() -> Optional[str]:
    """Return the content of the most recent daily summary, if any."""
    if not LOGS_DIR.exists():
        return None

    summaries = sorted(LOGS_DIR.glob("daily_summary_*.md"), reverse=True)
    if not summaries:
        return None

    return summaries[0].read_text(encoding="utf-8")


def should_generate_summary() -> bool:
    """Check if a daily summary should be generated now.

    Conditions:
    - Market is closed (or recently closed)
    - No summary exists for today
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = LOGS_DIR / f"daily_summary_{today_str}.md"
    return not output_file.exists()