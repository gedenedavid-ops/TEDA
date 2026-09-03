"""
Module 3 - Supply and Demand zones (Offre et Demande).

A supply zone is a HIGH delimited by a manipulative candle and/or a
"money-take" candle. A demand zone is a LOW delimited by the same
signatures.

Implementation approach (practical, SMC-style):

1. Detect "impulse" candles: bars with a body significantly larger than
   the rolling average body -> this is where the big players stepped in.
2. The 1..N bars immediately before a strong bullish impulse form the
   *demand* base (origin). The base's low..high is the demand zone.
3. Symmetrically for a strong bearish impulse -> supply zone.

Also handles breaker blocks (polarite inverse): a supply zone that gets
broken upward becomes demand, and a demand zone broken downward becomes
supply.

Timeframes: zones are read on H4 / H1.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from .models import SupplyDemandZone

# A bar whose body is >= this multiple of the rolling mean body is an impulse.
IMPULSE_BODY_MULT = 2.0
ROLLING_WINDOW = 20
BASE_BARS = 2  # number of bars forming the base before the impulse


def _bodies(df: pd.DataFrame) -> np.ndarray:
    return np.abs(df["close"].values - df["open"].values)


def detect_zones(
    df: pd.DataFrame,
    body_mult: float = IMPULSE_BODY_MULT,
    window: int = ROLLING_WINDOW,
    base_bars: int = BASE_BARS,
) -> List[SupplyDemandZone]:
    """Detect supply and demand zones from impulse candles."""
    close = df["close"].values
    open_ = df["open"].values
    high = df["high"].values
    low = df["low"].values
    body = _bodies(df)
    n = len(df)

    # Rolling mean body to scale the impulse threshold.
    mean_body = pd.Series(body).rolling(window, min_periods=window).mean().values

    zones: List[SupplyDemandZone] = []
    for i in range(window, n):
        mean = mean_body[i]
        if mean is None or np.isnan(mean) or mean == 0:
            continue

        bullish = close[i] > open_[i]
        is_impulse = body[i] >= body_mult * mean

        if not is_impulse:
            continue

        base_start = max(0, i - base_bars)
        base_high = float(np.max(high[base_start:i]))
        base_low = float(np.min(low[base_start:i]))

        if bullish:
            # Strong buying -> the base below is demand.
            zones.append(
                SupplyDemandZone(
                    zone_type="demand",
                    top=base_high,
                    bottom=base_low,
                    index=i,
                    timestamp=df.index[i],
                    origin="money_take",
                )
            )
        else:
            # Strong selling -> the base above is supply.
            zones.append(
                SupplyDemandZone(
                    zone_type="supply",
                    top=base_high,
                    bottom=base_low,
                    index=i,
                    timestamp=df.index[i],
                    origin="money_take",
                )
            )

    return zones


def detect_breaker_blocks(
    df: pd.DataFrame, zones: List[SupplyDemandZone]
) -> List[SupplyDemandZone]:
    """Return breaker blocks: zones whose polarity flips once broken.

    - A supply zone broken to the upside becomes a demand zone.
    - A demand zone broken to the downside becomes a supply zone.
    """
    close = df["close"].values
    breakers: List[SupplyDemandZone] = []

    for z in zones:
        # Look at bars after the zone origin to see if it was violated.
        for j in range(z.index + 1, len(df)):
            if z.zone_type == "supply" and close[j] > z.top:
                breakers.append(
                    SupplyDemandZone(
                        zone_type="demand",
                        top=z.top,
                        bottom=z.bottom,
                        index=j,
                        timestamp=df.index[j],
                        origin="breaker",
                    )
                )
                break
            if z.zone_type == "demand" and close[j] < z.bottom:
                breakers.append(
                    SupplyDemandZone(
                        zone_type="supply",
                        top=z.top,
                        bottom=z.bottom,
                        index=j,
                        timestamp=df.index[j],
                        origin="breaker",
                    )
                )
                break

    return breakers


def mark_mitigated(
    df: pd.DataFrame, zones: List[SupplyDemandZone]
) -> List[SupplyDemandZone]:
    """Flag zones the price has already reacted on (mitigated)."""
    low = df["low"].values
    high = df["high"].values

    for z in zones:
        for j in range(z.index + 1, len(df)):
            if z.zone_type == "demand" and low[j] <= z.top:
                z.mitigated = True
                break
            if z.zone_type == "supply" and high[j] >= z.bottom:
                z.mitigated = True
                break
    return zones
