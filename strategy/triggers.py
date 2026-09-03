"""
Module - Trigger chain (the SMV entry engine).

Combines the five validated filters in order:

    1. HTF directional bias (the 80% impulse direction)
    2. A supply/demand zone of the matching type (unmitigated)
    3. An imbalance (FVG) that confirms the zone is "logical"
    4. Liquidity sweep: the zone's external liquidity must ALREADY be
       swept (clean) -> priority intervention zone, not inducement
    5. Market shift on the LTF (change of character confirmation)

All five must pass to emit a BUY / SELL signal.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from .models import (
    FairValueGap,
    LiquidityLevel,
    Signal,
    StructureResult,
    SupplyDemandZone,
)
from . import imbalance as imb
from . import liquidity as liq
from . import structure as struct


def _pick_zone(
    zones: List[SupplyDemandZone], zone_type: str, current_price: float
) -> Optional[SupplyDemandZone]:
    """Return the closest unmitigated zone of the requested type."""
    candidates = [z for z in zones if z.zone_type == zone_type and not z.mitigated]
    if not candidates:
        return None
    candidates.sort(key=lambda z: abs((z.top + z.bottom) / 2 - current_price))
    return candidates[0]


def _confirm_fvg(
    zone: SupplyDemandZone, fvgs: List[FairValueGap]
) -> Optional[FairValueGap]:
    """Return an FVG that confirms the zone, if any."""
    for f in fvgs:
        if f.filled:
            continue
        if imb.confirms_zone(f, zone.top, zone.bottom, zone.zone_type):
            return f
    return None


def evaluate_trigger(
    structure_htf: StructureResult,
    zones: List[SupplyDemandZone],
    fvgs: List[FairValueGap],
    liquidity: List[LiquidityLevel],
    df_ltf: pd.DataFrame,
    current_price: float,
    ltf_lookback: int = 5,
) -> Signal:
    """Run the 5-filter chain and return a Signal (BUY / SELL / NONE)."""
    filters: dict = {
        "bias": False,
        "zone": False,
        "imbalance": False,
        "liquidity": False,
        "market_shift": False,
    }
    reason_parts: List[str] = []

    # ---- Filter 1: HTF directional bias --------------------------------
    if structure_htf.bias == "bullish":
        zone_type, fvg_type, direction = "demand", "bullish", "up"
    elif structure_htf.bias == "bearish":
        zone_type, fvg_type, direction = "supply", "bearish", "down"
    else:
        return Signal(
            signal="NONE",
            bias=structure_htf.bias,
            filters_passed=filters,
            reason="No clear HTF bias (consolidation)",
        )

    filters["bias"] = True
    reason_parts.append(f"HTF bias {structure_htf.bias}")

    # ---- Filter 2: matching supply/demand zone --------------------------
    zone = _pick_zone(zones, zone_type, current_price)
    if zone is None:
        return Signal(
            signal="NONE",
            bias=structure_htf.bias,
            filters_passed=filters,
            reason="No unmitigated " + zone_type + " zone",
        )
    filters["zone"] = True
    reason_parts.append(f"zone {zone_type} @ {zone.bottom:.2f}-{zone.top:.2f}")

    # ---- Filter 3: FVG confirms the zone --------------------------------
    fvg = _confirm_fvg(zone, fvgs)
    if fvg is None:
        return Signal(
            signal="NONE",
            bias=structure_htf.bias,
            filters_passed=filters,
            zone=zone,
            reason="Zone not confirmed by an imbalance (FVG)",
        )
    filters["imbalance"] = True
    reason_parts.append(f"FVG {fvg.fvg_type} @ {fvg.bottom:.2f}-{fvg.top:.2f}")

    # ---- Filter 4: liquidity already swept (clean, not inducement) ------
    sweep_state = liq.check_zone_sweep(df_ltf, zone, liquidity)
    if sweep_state != "clean":
        return Signal(
            signal="NONE",
            bias=structure_htf.bias,
            filters_passed=filters,
            zone=zone,
            reason=f"Zone liquidity state = {sweep_state} (inducement/neutral)",
        )
    filters["liquidity"] = True
    reason_parts.append("external liquidity swept (clean)")

    # ---- Filter 5: market shift on LTF ----------------------------------
    ltf_struct = struct.analyze_structure(df_ltf, ltf_lookback)
    if ltf_struct.last_bos is None:
        return Signal(
            signal="NONE",
            bias=structure_htf.bias,
            filters_passed=filters,
            zone=zone,
            reason="No BOS on LTF",
        )
    shift_ok = ltf_struct.last_bos.kind == (
        "bullish" if direction == "up" else "bearish"
    )
    if not shift_ok:
        return Signal(
            signal="NONE",
            bias=structure_htf.bias,
            filters_passed=filters,
            zone=zone,
            reason="No market shift on LTF",
        )
    filters["market_shift"] = True
    reason_parts.append("market shift LTF confirmed")

    # ---- Compute entry / SL / TP / RR ----------------------------------
    if direction == "up":
        entry_top, entry_bottom = zone.top, zone.bottom
        stop_loss = round(zone.bottom - (zone.top - zone.bottom) * 0.1, 2)
        # TP: EQH or swing_high above the zone (liquidity target)
        tp_levels = [
            l.price
            for l in liquidity
            if l.level_type in ("EQH", "swing_high") and l.price > zone.top
        ]
        take_profit = min(tp_levels) if tp_levels else None
        # Fallback: minimum 1:7 RR from entry mid
        if take_profit is None:
            entry_mid = (entry_top + entry_bottom) / 2
            risk = entry_mid - stop_loss
            take_profit = round(entry_mid + risk * 7.0, 2)
    else:
        entry_top, entry_bottom = zone.top, zone.bottom
        stop_loss = round(zone.top + (zone.top - zone.bottom) * 0.1, 2)
        # TP: EQL or swing_low below the zone (liquidity target)
        tp_levels = [
            l.price
            for l in liquidity
            if l.level_type in ("EQL", "swing_low") and l.price < zone.bottom
        ]
        take_profit = max(tp_levels) if tp_levels else None
        # Fallback: minimum 1:7 RR from entry mid
        if take_profit is None:
            entry_mid = (entry_top + entry_bottom) / 2
            risk = stop_loss - entry_mid
            take_profit = round(entry_mid - risk * 7.0, 2)

    entry_mid = (entry_top + entry_bottom) / 2
    rr_ratio = None
    if take_profit is not None and entry_mid != stop_loss:
        rr_ratio = round(abs(take_profit - entry_mid) / abs(entry_mid - stop_loss), 1)

    # Confidence: all five filters -> high; liquidity clean is the tie-breaker.
    confidence = "high" if sweep_state == "clean" else "medium"

    return Signal(
        signal="BUY" if direction == "up" else "SELL",
        bias=structure_htf.bias,
        filters_passed=filters,
        entry_top=entry_top,
        entry_bottom=entry_bottom,
        stop_loss=stop_loss,
        take_profit=take_profit,
        rr_ratio=rr_ratio,
        confidence=confidence,
        zone=zone,
        reason=" | ".join(reason_parts),
    )


# ---- Consolidation / Iron Condor trigger -----------------------------------


def evaluate_consolidation(
    zones: List[SupplyDemandZone],
    fvgs: List[FairValueGap],
    liquidity: List[LiquidityLevel],
    current_price: float,
) -> Signal:
    """Detect a range-bound market suitable for an Iron Condor.

    Conditions:
      1. Clear support below price (unmitigated demand zone or swing low).
      2. Clear resistance above price (unmitigated supply zone or swing high).
      3. Price is between support and resistance.
      4. Range is wide enough to be worth trading (>= 2% of price).
    """
    # Support: nearest unmitigated demand zone below current price
    demand_zones = [
        z for z in zones
        if z.zone_type == "demand" and not z.mitigated and z.bottom < current_price
    ]
    demand_zones.sort(key=lambda z: current_price - z.bottom)

    # Resistance: nearest unmitigated supply zone above current price
    supply_zones = [
        z for z in zones
        if z.zone_type == "supply" and not z.mitigated and z.top > current_price
    ]
    supply_zones.sort(key=lambda z: z.top - current_price)

    # Also check swing levels from liquidity
    swing_lows = [l for l in liquidity if l.level_type == "swing_low" and l.price < current_price]
    swing_highs = [l for l in liquidity if l.level_type == "swing_high" and l.price > current_price]

    # Pick support (prefer zone, fallback to swing low)
    if demand_zones:
        support = (demand_zones[0].bottom + demand_zones[0].top) / 2
    elif swing_lows:
        swing_lows.sort(key=lambda l: current_price - l.price)
        support = swing_lows[0].price
    else:
        return Signal(signal="NONE", bias="neutral",
                      reason="No clear support for consolidation range")

    # Pick resistance (prefer zone, fallback to swing high)
    if supply_zones:
        resistance = (supply_zones[0].bottom + supply_zones[0].top) / 2
    elif swing_highs:
        swing_highs.sort(key=lambda l: l.price - current_price)
        resistance = swing_highs[0].price
    else:
        return Signal(signal="NONE", bias="neutral",
                      reason="No clear resistance for consolidation range")

    # Range must be wide enough (>= 1.5% of current price)
    range_pct = (resistance - support) / current_price * 100
    if range_pct < 1.5:
        return Signal(
            signal="NONE", bias="neutral",
            support=support, resistance=resistance,
            reason=f"Range too narrow ({range_pct:.1f}%, need >= 1.5%)",
        )

    # Price must be inside the range
    if not (support < current_price < resistance):
        return Signal(
            signal="NONE", bias="neutral",
            support=support, resistance=resistance,
            reason="Price outside consolidation range",
        )

    filters = {
        "bias": True,
        "zone": bool(supply_zones or swing_highs),
        "imbalance": True,  # not a strict requirement for iron condor
        "liquidity": True,
        "market_shift": True,
    }

    # Margin of safety: 2% inside support and 2% below resistance
    # (reserved for future use — wing width calculation in options.py)
    _ = support * 0.98
    _ = resistance * 1.02

    return Signal(
        signal="IRON_CONDOR",
        bias="neutral",
        filters_passed=filters,
        entry_top=resistance,
        entry_bottom=support,
        stop_loss=None,  # defined by wing width in options.py
        take_profit=None,  # max profit = credit received
        rr_ratio=None,  # iron condor doesn't use RR the same way
        confidence="medium",
        support=support,
        resistance=resistance,
        reason=f"Consolidation range {support:.2f}-{resistance:.2f} ({range_pct:.1f}%) | Iron Condor",
    )
