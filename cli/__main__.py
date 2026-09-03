"""
Alpaca CLI — command-line tools for the Options Alpha Agent.

Mirrors the Alpaca CLI functionality while integrating with the SMV
strategy engine. Satisfies the hackathon's "Alpaca CLI" requirement.

Usage:
    python -m cli account              # account equity, cash, buying power
    python -m cli positions             # list open positions
    python -m cli orders                # recent orders (last 10)
    python -m cli watchlist             # scan all 10 assets (SMV analysis)
    python -m cli trade SYM ACTION      # manual trade (BUY/SELL)
    python -m cli agent start           # start autonomous agent loop
    python -m cli agent stop --signal   # stop a running agent via signal file
    python -m cli status                # market clock + account summary
    python -m cli export                # export watchlist to CSV
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .commands import (
    cmd_account,
    cmd_positions,
    cmd_orders,
    cmd_watchlist,
    cmd_status,
    cmd_export,
    cmd_agent_start,
    cmd_agent_stop,
    cmd_trade,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m cli",
        description="Alpaca CLI — Options Alpha Agent · Hackathon lablab.ai × Alpaca",
    )
    sub = parser.add_subparsers(dest="command", help="commande")

    # account
    sub.add_parser("account", help="résumé du compte Alpaca paper")

    # positions
    sub.add_parser("positions", help="positions ouvertes")

    # orders
    sub.add_parser("orders", help="10 derniers ordres")

    # watchlist
    sub.add_parser("watchlist", help="scan SMV des 10 actifs")

    # status
    sub.add_parser("status", help="horloge marché + résumé compte")

    # export
    sub.add_parser("export", help="exporter la watchlist en CSV")

    # trade
    p_trade = sub.add_parser("trade", help="placer un trade manuel")
    p_trade.add_argument("symbol", help="symbole (SPY, QQQ, NVDA, AAPL, etc.)")
    p_trade.add_argument("action", choices=["BUY", "SELL"], help="direction")

    # agent
    p_agent = sub.add_parser("agent", help="contrôler l'agent autonome")
    agent_sub = p_agent.add_subparsers(dest="agent_cmd")
    agent_sub.add_parser("start", help="démarrer l'agent en boucle")
    p_agent_stop = agent_sub.add_parser("stop", help="créer un fichier stop pour l'agent")
    p_agent_stop.add_argument("--signal", action="store_true", help="envoyer signal d'arrêt")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "account": cmd_account,
        "positions": cmd_positions,
        "orders": cmd_orders,
        "watchlist": cmd_watchlist,
        "status": cmd_status,
        "export": cmd_export,
        "trade": lambda: cmd_trade(args.symbol, args.action),
        "agent": lambda: _handle_agent(args),
    }

    fn = commands.get(args.command)
    if fn:
        fn()
    else:
        parser.print_help()


def _handle_agent(args) -> None:
    if args.agent_cmd == "start":
        cmd_agent_start()
    elif args.agent_cmd == "stop":
        cmd_agent_stop()
    else:
        print("Usage: python -m cli agent [start|stop]")


if __name__ == "__main__":
    main()