"""
Decision engine: LLM reasoning + trade journaling.

The Featherless LLM (open-source) explains *why* a trade was taken and
writes a human-readable journal entry. It does NOT place orders: the SMV
rules are deterministic and remain the source of truth for execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from strategy.models import Signal

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
TRADE_LOG = LOGS_DIR / "trades.md"


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


def reason_about_signal(
    signal: Signal,
    symbol: str,
    price: float,
) -> str:
    """Ask the LLM to explain the decision. Falls back to a summary."""
    client = _get_llm_client()
    if client is None:
        return _fallback_summary(signal, symbol, price)

    from config.settings import settings

    prompt = (
        f"Tu es un analyste de trading Smart Money Concepts. Explique en 3-4 "
        f"phrases courtes et factuelles le signal suivant, sans donner de "
        f"conseil financier.\n\n"
        f"Symbole: {symbol} @ {price:.2f}\n"
        f"Signal: {signal.signal} (biais {signal.bias})\n"
        f"Filtres passés: {signal.filters_passed}\n"
        f"Entrée: {signal.entry_bottom:.2f}-{signal.entry_top:.2f}\n"
        f"Stop: {signal.stop_loss}, TP: {signal.take_profit}, RR: {signal.rr_ratio}\n"
        f"Raison technique: {signal.reason}\n"
    )

    try:
        resp = client.chat.completions.create(
            model=settings.featherless_model,
            messages=[
                {"role": "system", "content": "Réponds de façon concise."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:  # network / auth / model error -> fallback
        return f"[LLM indisponible: {exc}] " + _fallback_summary(signal, symbol, price)


def _fallback_summary(signal: Signal, symbol: str, price: float) -> str:
    return (
        f"{signal.signal} {symbol} @ {price:.2f} "
        f"(biais {signal.bias}, RR {signal.rr_ratio}, "
        f"entrée {signal.entry_bottom:.2f}-{signal.entry_top:.2f})"
    )


def log_decision(
    signal: Signal,
    symbol: str,
    price: float,
    action: str,
    reasoning: str = "",
) -> None:
    """Append a timestamped trade decision to the journal."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"## {ts} — {signal.signal} {symbol}",
        f"- **Action** : {action}",
        f"- **Prix** : {price:.2f}",
        f"- **Biais** : {signal.bias}",
        f"- **Filtres** : {signal.filters_passed}",
        f"- **Entrée** : {signal.entry_bottom:.2f} - {signal.entry_top:.2f}",
        f"- **SL / TP** : {signal.stop_loss} / {signal.take_profit}",
        f"- **RR** : {signal.rr_ratio}",
        f"- **Confiance** : {signal.confidence}",
        f"- **Raison** : {signal.reason}",
    ]
    if reasoning:
        lines.append(f"- **Analyse IA** : {reasoning}")
    lines.append("")

    with open(TRADE_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
