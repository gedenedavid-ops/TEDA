"""
Module 5 - Liquidity (and the sweep "triage" of zones).

Liquidity is what the "big boys" hunt before the real move:

- EQL (Equal Lows)  : swing lows at the same level -> sell-side liquidity
- EQH (Equal Highs) : swing highs at the same level -> buy-side liquidity
- Trendline liquidity: several highs/lows connected by a line

The core SMV rule implemented here:

    A demand zone whose external (sell-side) liquidity has ALREADY been
    swept by a wick/impulse becomes the PRIORITY intervention zone (the
    liquidity trap has been purged). Conversely, a zone whose liquidity
    is still sitting "in front" of it is Inducement (a trap) and should
    be treated with caution.

Timeframes: liquidity is read on H1 / M15.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from .models import LiquidityLevel, SupplyDemandZone
from .structure import detect_swing_points

EQL_TOLERANCE = 0.001  # 0.1% price tolerance to consider two lows "equal"


def detect_equal_levels(
    df: pd.DataFrame, lookback: int = 5, tolerance: float = EQL_TOLERANCE
) -> List[LiquidityLevel]:
    """Detect Equal Lows (EQL) and Equal Highs (EQH) from swing points."""
    swings = detect_swing_points(df, lookback)
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]

    levels: List[LiquidityLevel] = []
    levels.extend(_cluster(highs, "EQH", tolerance))
    levels.extend(_cluster(lows, "EQL", tolerance))
    return levels


def _cluster(
    points: list, level_type: str, tolerance: float
) -> List[LiquidityLevel]:
    """Group swing points that sit at the same price into liquidity levels."""
    if not points:
        return []

    levels: List[LiquidityLevel] = []
    points = sorted(points, key=lambda p: p.price)

    cluster = [points[0]]
    for p in points[1:]:
        ref = cluster[-1].price
        if abs(p.price - ref) / ref <= tolerance:
            cluster.append(p)
        else:
            if len(cluster) >= 2:  # "equal" requires at least two points
                levels.append(_to_level(cluster, level_type))
            cluster = [p]

    if len(cluster) >= 2:
        levels.append(_to_level(cluster, level_type))

    return levels


def _to_level(cluster: list, level_type: str) -> LiquidityLevel:
    avg_price = float(np.mean([p.price for p in cluster]))
    last = cluster[-1]
    return LiquidityLevel(
        level_type=level_type,
        price=avg_price,
        index=last.index,
        timestamp=last.timestamp,
    )


def mark_sweeps(
    df: pd.DataFrame, levels: List[LiquidityLevel]
) -> List[LiquidityLevel]:
    """Mark a liquidity level as swept if a later wick pierces it and closes back.

    - EQH / buy-side : a later candle's HIGH pierces the level, close is below it.
    - EQL / sell-side: a later candle's LOW pierces the level, close is above it.
    """
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values

    for lvl in levels:
        for j in range(lvl.index + 1, len(df)):
            if lvl.level_type in ("EQH", "swing_high"):
                if high[j] > lvl.price and close[j] < lvl.price:
                    lvl.swept = True
                    break
            else:  # EQL / swing_low
                if low[j] < lvl.price and close[j] > lvl.price:
                    lvl.swept = True
                    break

    return levels


def analyze_liquidity(
    df: pd.DataFrame, lookback: int = 5, tolerance: float = EQL_TOLERANCE
) -> List[LiquidityLevel]:
    """Detect and annotate all liquidity levels."""
    levels = detect_equal_levels(df, lookback, tolerance)
    return mark_sweeps(df, levels)


def check_zone_sweep(
    df: pd.DataFrame,
    zone: SupplyDemandZone,
    levels: List[LiquidityLevel],
) -> str:
    """Classify a supply/demand zone vs its external liquidity.

    Returns one of:
      - "clean"     : external liquidity already swept -> PRIORITY zone
      - "inducement": liquidity still in front -> trap, treat with caution
      - "neutral"   : no relevant external liquidity detected
    """
    close = df["close"].values
    n = len(df)

    if zone.zone_type == "demand":
        # Sell-side liquidity BELOW the demand zone.
        externals = [l for l in levels if l.price < zone.bottom and l.level_type == "EQL"]
        if not externals:
            return "neutral"
        # Swept if a wick already pierced the level and closed back.
        for l in externals:
            for j in range(l.index + 1, n):
                if df["low"].values[j] < l.price and close[j] > l.price:
                    return "clean"
        return "inducement"

    # Supply zone: buy-side liquidity ABOVE it.
    externals = [l for l in levels if l.price > zone.top and l.level_type == "EQH"]
    if not externals:
        return "neutral"
    for l in externals:
        for j in range(l.index + 1, n):
            if df["high"].values[j] > l.price and close[j] < l.price:
                return "clean"
    return "inducement"
