"""
Options execution: map SMV signals to the trader's chosen strategies.

B/B/B rules:
- BUY  -> Call Debit Spread  (B)
- SELL -> Put Debit Spread   (B)
- Consolidation -> Iron Condor (B) — handled separately.

Each spread is built as a multi-leg order on Alpaca.
"""

from __future__ import annotations

from typing import List, Optional

from alpaca.trading.enums import (
    AssetClass,
    ContractType,
    OrderClass,
    OrderSide,
    OrderType,
    PositionIntent,
    TimeInForce,
)
from alpaca.trading.models import OptionContract
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    LimitOrderRequest,
    OptionLegRequest,
)

from config.settings import settings
from execution.client import BrokerClient


def _current_date():
    from datetime import date
    return date.today()


def _get_strikes(
    broker: BrokerClient,
    underlying: str,
    contract_type: str,
    dte_min: int = settings.default_dte_min,
    dte_max: int = settings.default_dte_max,
) -> List[OptionContract]:
    """Fetch tradable option contracts for an underlying within the DTE band."""
    contracts = broker.trading.get_option_contracts(
        GetOptionContractsRequest(
            underlying_symbols=[underlying],
            type=contract_type,
            expiration_date_gte=_current_date().isoformat(),
            limit=1000,  # enough to cover multiple expirations
        )
    )
    candidates = []
    close = []  # contracts too close to expiry (for debugging)
    for c in contracts.option_contracts or []:
        if not c.tradable:
            continue
        dte = (c.expiration_date - _current_date()).days
        if dte_min <= dte <= dte_max:
            candidates.append(c)
        elif 0 <= dte < dte_min:
            close.append(c)

    # Fallback: expand range but NEVER pick contracts expiring today (dte < 2)
    if not candidates:
        for c in contracts.option_contracts or []:
            if not c.tradable:
                continue
            dte = (c.expiration_date - _current_date()).days
            if dte >= 2:  # at least 2 days to expiry
                candidates.append(c)

    if not candidates:
        print(f"  [options] aucun contrat tradable avec DTE >= 2 pour {underlying} {contract_type}")
        if close:
            print(f"  [options] {len(close)} contrats trop proches (DTE < {dte_min}), ignorés")

    candidates.sort(key=lambda c: float(c.strike_price))
    return candidates


def _pick_strike(
    candidates: List[OptionContract], target_price: float
) -> Optional[OptionContract]:
    """Pick the contract whose strike is closest to the target price."""
    if not candidates:
        return None
    candidates.sort(key=lambda c: abs(float(c.strike_price) - target_price))
    return candidates[0]


def _pick_strike_offset(
    candidates: List[OptionContract], base_price: float, offset: float
) -> Optional[OptionContract]:
    """Pick a strike offset from base_price (positive = higher, negative = lower)."""
    target = base_price + offset
    return _pick_strike(candidates, target)


def contract_type_for_signal(signal_str: str) -> str:
    return "call" if signal_str == "BUY" else "put"


# ---- Debit Spread ----------------------------------------------------------


def build_debit_spread(
    broker: BrokerClient,
    underlying: str,
    signal,  # Signal model
    risk_amount: float,
) -> Optional[MarketOrderRequest]:
    """Build a Call (BUY) or Put (SELL) debit spread.

    - Long leg at strike near the entry zone.
    - Short leg at strike near the take-profit level.
    - Debit paid = risk capped per position sizing.
    """
    ct = contract_type_for_signal(signal.signal)
    candidates = _get_strikes(broker, underlying, ct)

    entry_mid = (signal.entry_top + signal.entry_bottom) / 2
    long_leg = _pick_strike(candidates, entry_mid)
    if long_leg is None:
        return None

    tp = signal.take_profit
    if tp is None:
        tp = entry_mid * 1.05 if ct == "call" else entry_mid * 0.95

    short_leg = _pick_strike(candidates, tp)
    if short_leg is None:
        # Fallback: 2 strikes away from the long leg.
        idx = candidates.index(long_leg) if long_leg in candidates else 0
        short_idx = min(idx + 2, len(candidates) - 1)
        short_leg = candidates[short_idx]

    long_strike = float(long_leg.strike_price)
    short_strike = float(short_leg.strike_price)

    # Debit paid = max loss for a debit spread.
    # The actual debit is typically 30-50% of the spread width.
    # We use 40% for risk sizing and 50% as the limit price.
    width = abs(long_strike - short_strike)
    if width == 0:
        return None
    estimated_debit = round(width * 0.40, 2)   # realistic risk per share
    max_loss_per_contract = estimated_debit * 100
    qty = max(1, int(risk_amount // max_loss_per_contract))

    legs = [
        OptionLegRequest(
            symbol=long_leg.symbol,
            ratio_qty=qty,
            side=OrderSide.BUY,
            position_intent=PositionIntent.BUY_TO_OPEN,
        ),
        OptionLegRequest(
            symbol=short_leg.symbol,
            ratio_qty=qty,
            side=OrderSide.SELL,
            position_intent=PositionIntent.SELL_TO_OPEN,
        ),
    ]

    limit_price = round(width * 0.50, 2)  # generous limit for fill safety
    return LimitOrderRequest(
        legs=legs,
        limit_price=limit_price,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.MLEG,
        qty=qty,
    )


# ---- Iron Condor -----------------------------------------------------------


def build_iron_condor(
    broker: BrokerClient,
    underlying: str,
    current_price: float,
    support: float,
    resistance: float,
    risk_amount: float,
) -> Optional[MarketOrderRequest]:
    """Build an Iron Condor for consolidation phases.

    - Sell a put spread below support (sell put at K1, buy put at K2 lower).
    - Sell a call spread above resistance (sell call at K3, buy call at K4 higher).
    - Credit received = max profit.
    """
    puts = _get_strikes(broker, underlying, "put")
    calls = _get_strikes(broker, underlying, "call")

    if not puts or not calls:
        return None

    # Put spread: short near support, long further below.
    short_put = _pick_strike(puts, support * 0.98)
    long_put = _pick_strike(puts, support * 0.95)
    # Call spread: short near resistance, long further above.
    short_call = _pick_strike(calls, resistance * 1.02)
    long_call = _pick_strike(calls, resistance * 1.05)

    if not all([short_put, long_put, short_call, long_call]):
        return None

    put_width = abs(float(short_put.strike_price) - float(long_put.strike_price))
    call_width = abs(float(short_call.strike_price) - float(long_call.strike_price))
    wing = max(put_width, call_width)
    # Iron condor: max loss = wing - credit. Credit ~20% of wing.
    max_loss_per_contract = round(wing * 100 * 0.80, 2)
    qty = max(1, int(risk_amount // max_loss_per_contract))

    legs = [
        OptionLegRequest(symbol=short_put.symbol, ratio_qty=qty,
                         side=OrderSide.SELL, position_intent=PositionIntent.SELL_TO_OPEN),
        OptionLegRequest(symbol=long_put.symbol, ratio_qty=qty,
                         side=OrderSide.BUY, position_intent=PositionIntent.BUY_TO_OPEN),
        OptionLegRequest(symbol=short_call.symbol, ratio_qty=qty,
                         side=OrderSide.SELL, position_intent=PositionIntent.SELL_TO_OPEN),
        OptionLegRequest(symbol=long_call.symbol, ratio_qty=qty,
                         side=OrderSide.BUY, position_intent=PositionIntent.BUY_TO_OPEN),
    ]

    credit = round(wing * 0.20, 2)  # min credit per share we accept
    return LimitOrderRequest(
        legs=legs,
        limit_price=credit,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.MLEG,
        qty=qty,
    )
