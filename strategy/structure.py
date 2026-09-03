"""
Module 1 - Structure is Queen (SMV).

Detects market structure and the 80/20 impulse/retracement split:

- Swing highs / swing lows
- Bullish (HH + HL), Bearish (LH + LL), Consolidation
- Break of Structure (BOS): classic / continuation / trap
- Directional bias: the 80% impulse direction vs the 20% retracement
- Market shift (LTF reaction above/below a broken level)

Timeframes: structure is read on HTF (D1 / H4).
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from .models import BOSEvent, StructureResult, SwingPoint


def detect_swing_points(df: pd.DataFrame, lookback: int = 5) -> List[SwingPoint]:
    """Return local swing highs and lows using a symmetric window.

    A bar is a swing high if its high is the max of the surrounding
    ``lookback`` bars on each side (and symmetrically for lows).
    """
    swings: List[SwingPoint] = []
    high = df["high"].values
    low = df["low"].values
    n = len(df)

    for i in range(lookback, n - lookback):
        window_high = high[i - lookback : i + lookback + 1]
        window_low = low[i - lookback : i + lookback + 1]

        if high[i] == window_high.max():
            swings.append(SwingPoint(i, df.index[i], float(high[i]), "high"))
        if low[i] == window_low.min():
            swings.append(SwingPoint(i, df.index[i], float(low[i]), "low"))

    swings.sort(key=lambda s: s.index)
    return swings


def classify_structure(
    df: pd.DataFrame, lookback: int = 5, num_swings: int = 2
) -> str:
    """Classify structure as bullish / bearish / neutral.

    Uses the last ``num_swings`` swing highs and lows.
    """
    swings = detect_swing_points(df, lookback)
    highs = [s for s in swings if s.kind == "high"][-num_swings:]
    lows = [s for s in swings if s.kind == "low"][-num_swings:]

    if len(highs) < num_swings or len(lows) < num_swings:
        return "neutral"

    hh = all(highs[i].price > highs[i - 1].price for i in range(1, len(highs)))
    hl = all(lows[i].price > lows[i - 1].price for i in range(1, len(lows)))
    lh = all(highs[i].price < highs[i - 1].price for i in range(1, len(highs)))
    ll = all(lows[i].price < lows[i - 1].price for i in range(1, len(lows)))

    if hh and hl:
        return "bullish"
    if lh and ll:
        return "bearish"
    return "neutral"


def detect_bos(
    df: pd.DataFrame, lookback: int = 5, trap_bars: int = 3
) -> List[BOSEvent]:
    """Detect Break of Structure events.

    A candle closing beyond the last unbroken swing high/low is a BOS.
    The type is inferred from the direction of the previous break:

    - ``classic``      : break against the current trend (change of character)
    - ``continuation`` : break in the same direction as the current trend
    - ``trap``         : a break that reverses within ``trap_bars`` candles

    Note: ``trap`` requires future bars, so it is only annotated in hindsight
    (fine for historical analysis / backtesting).
    """
    swings = detect_swing_points(df, lookback)
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]

    if not highs or not lows:
        return []

    events: List[BOSEvent] = []
    close = df["close"].values
    hi = li = 0
    last_high: Optional[SwingPoint] = None
    last_low: Optional[SwingPoint] = None
    trend: Optional[str] = None  # "bullish" | "bearish"

    for i in range(len(df)):
        # Advance swing trackers up to the current bar.
        while hi < len(highs) and highs[hi].index <= i:
            last_high = highs[hi]
            hi += 1
        while li < len(lows) and lows[li].index <= i:
            last_low = lows[li]
            li += 1

        if last_high is None or last_low is None:
            continue

        if close[i] > last_high.price:
            bos_type = "continuation" if trend == "bullish" else "classic"
            if trend is None:
                bos_type = "classic"
            events.append(
                BOSEvent(i, df.index[i], "bullish", bos_type, last_high.price)
            )
            trend = "bullish"
        elif close[i] < last_low.price:
            bos_type = "continuation" if trend == "bearish" else "classic"
            if trend is None:
                bos_type = "classic"
            events.append(
                BOSEvent(i, df.index[i], "bearish", bos_type, last_low.price)
            )
            trend = "bearish"

    return _annotate_traps(df, events, trap_bars)


def _annotate_traps(
    df: pd.DataFrame, events: List[BOSEvent], trap_bars: int
) -> List[BOSEvent]:
    """Mark a BOS as a trap if price reverts through the level quickly."""
    close = df["close"].values
    n = len(df)
    for ev in events:
        end = min(ev.index + trap_bars + 1, n)
        if ev.kind == "bullish" and any(c < ev.level for c in close[ev.index + 1 : end]):
            ev.bos_type = "trap"
        elif ev.kind == "bearish" and any(c > ev.level for c in close[ev.index + 1 : end]):
            ev.bos_type = "trap"
    return events


def detect_market_shift(
    df_ltf: pd.DataFrame, level: float, direction: str, lookback: int = 5
) -> bool:
    """Detect a market shift on a lower timeframe.

    ``direction`` = "up"   -> price closes back above ``level`` (bullish shift)
    ``direction`` = "down" -> price closes back below ``level`` (bearish shift)
    """
    close = df_ltf["close"].values
    if direction == "up":
        return bool(np.any(close[-lookback:] > level))
    if direction == "down":
        return bool(np.any(close[-lookback:] < level))
    return False


def analyze_structure(
    df: pd.DataFrame, lookback: int = 5, num_swings: int = 2
) -> StructureResult:
    """Full structural read of a single timeframe."""
    bias = classify_structure(df, lookback, num_swings)
    swings = detect_swing_points(df, lookback)
    bos_events = detect_bos(df, lookback)

    if bias == "bullish":
        impulse, retrace = "up", "down"
    elif bias == "bearish":
        impulse, retrace = "down", "up"
    else:
        impulse, retrace = "flat", "flat"

    last_bos = bos_events[-1] if bos_events else None

    # Market shift: price reacts beyond the most recent BOS level.
    market_shift = False
    if last_bos is not None:
        direction = "up" if last_bos.kind == "bullish" else "down"
        market_shift = detect_market_shift(df, last_bos.level, direction, lookback)

    return StructureResult(
        bias=bias,
        impulse_direction=impulse,
        retrace_direction=retrace,
        swings=swings,
        bos_events=bos_events,
        last_bos=last_bos,
        market_shift=market_shift,
    )
