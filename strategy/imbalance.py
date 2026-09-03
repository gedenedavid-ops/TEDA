"""
Module 6 - Imbalance / IPA (Fair Value Gap).

A Fair Value Gap (also called IPA - Inefficiency Price Action) is a
3-candle imbalance where the wicks of candle 1 and candle 3 do not
overlap, leaving a "gap" that price tends to revisit and fill.

- Bullish FVG : high[i-2] < low[i]   (aggressive buying)
- Bearish FVG : low[i-2] > high[i]   (aggressive selling)

In the SMV chain the imbalance is NOT an entry signal on its own:
it *confirms* a nearby supply/demand zone (making it "logical") and
gives us a precise retracement target.

Timeframes: imbalance is read on H1 / M15.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from .models import FairValueGap


def detect_fvg(df: pd.DataFrame) -> List[FairValueGap]:
    """Detect all Fair Value Gaps in the series (3-candle pattern)."""
    high = df["high"].values
    low = df["low"].values
    n = len(df)
    fvgs: List[FairValueGap] = []

    for i in range(2, n):
        # Bullish FVG: candle 1 high below candle 3 low.
        if high[i - 2] < low[i]:
            fvgs.append(
                FairValueGap(
                    fvg_type="bullish",
                    top=float(low[i]),
                    bottom=float(high[i - 2]),
                    index=i,
                    timestamp=df.index[i],
                )
            )
        # Bearish FVG: candle 1 low above candle 3 high.
        elif low[i - 2] > high[i]:
            fvgs.append(
                FairValueGap(
                    fvg_type="bearish",
                    top=float(high[i]),
                    bottom=float(low[i - 2]),
                    index=i,
                    timestamp=df.index[i],
                )
            )

    return fvgs


def mark_filled(df: pd.DataFrame, fvgs: List[FairValueGap]) -> List[FairValueGap]:
    """Flag FVGs whose zone has been traded back into (filled)."""
    low = df["low"].values
    high = df["high"].values

    for f in fvgs:
        for j in range(f.index + 1, len(df)):
            # A candle overlapping the gap zone fills it.
            if f.fvg_type == "bullish" and low[j] <= f.top and high[j] >= f.bottom:
                f.filled = True
                break
            if f.fvg_type == "bearish" and low[j] <= f.top and high[j] >= f.bottom:
                f.filled = True
                break
    return fvgs


def find_nearest_unfilled(
    fvgs: List[FairValueGap], current_price: float, fvg_type: Optional[str] = None
) -> Optional[FairValueGap]:
    """Return the nearest unfilled FVG of the given type, by zone distance."""
    candidates = [
        f for f in fvgs if not f.filled and (fvg_type is None or f.fvg_type == fvg_type)
    ]
    if not candidates:
        return None

    def distance(f: FairValueGap) -> float:
        if f.fvg_type == "bullish":
            # Above or below: we want the gap just below price.
            return current_price - f.bottom if current_price > f.bottom else float("inf")
        return f.top - current_price if current_price < f.top else float("inf")

    candidates.sort(key=distance)
    return candidates[0]


def confirms_zone(
    fvg: FairValueGap, zone_top: float, zone_bottom: float, zone_type: str
) -> bool:
    """Return True if the FVG overlaps or sits adjacent to a supply/demand zone.

    A bullish FVG aligned with a demand zone (or bearish FVG with a supply
    zone) makes the zone more "logical" per the SMV rules.
    """
    if fvg.fvg_type == "bullish" and zone_type == "demand":
        # FVG inside or just below the demand zone.
        return fvg.bottom <= zone_top and fvg.top >= zone_bottom * 0.99
    if fvg.fvg_type == "bearish" and zone_type == "supply":
        return fvg.top >= zone_bottom and fvg.bottom <= zone_top * 1.01
    return False


def analyze_imbalance(df: pd.DataFrame) -> List[FairValueGap]:
    """Detect and annotate all FVGs."""
    fvgs = detect_fvg(df)
    return mark_filled(df, fvgs)
