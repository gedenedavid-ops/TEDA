"""
Risk management (SMV rules).

- Risk max 1% of equity per trade.
- Minimum reward/risk 1:7.
- Position size derived from the stop-loss distance (or premium paid for
  long options).
"""

from __future__ import annotations

from typing import Optional

from config.settings import settings
from strategy.models import Signal


def compute_risk_amount(equity: float, risk_pct: Optional[float] = None) -> float:
    """Dollar amount at risk for one trade (default 1% of equity)."""
    pct = settings.risk_per_trade_pct if risk_pct is None else risk_pct
    return equity * pct


def check_rr_ratio(signal: Signal, min_rr: Optional[float] = None) -> bool:
    """Validate the signal meets the minimum reward/risk ratio."""
    threshold = settings.min_rr_ratio if min_rr is None else min_rr
    if signal.rr_ratio is None:
        return False
    return signal.rr_ratio >= threshold


def max_position_notional(equity: float) -> float:
    """Maximum notional allowed for a single position (default 25%)."""
    return equity * settings.max_position_pct
