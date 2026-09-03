"""
Shared data models for the SMV (Smart Money Vision) strategy engine.

These dataclasses are the common "currency" exchanged between the
detection modules (structure, supply_demand, imbalance, liquidity)
and the final trigger chain (triggers.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# ---- Type aliases ----------------------------------------------------------

Bias = str            # "bullish" | "bearish" | "neutral"
ZoneType = str         # "demand" | "supply"
FVGType = str          # "bullish" | "bearish"
SignalType = str       # "BUY" | "SELL" | "IRON_CONDOR" | "NONE"


# ---- Structure -------------------------------------------------------------


@dataclass
class SwingPoint:
    """A local extremum used to read market structure."""

    index: int
    timestamp: object
    price: float
    kind: str  # "high" | "low"


@dataclass
class BOSEvent:
    """Break of Structure event (classic / continuation / trap)."""

    index: int
    timestamp: object
    kind: str        # "bullish" | "bearish"
    bos_type: str    # "classic" | "continuation" | "trap"
    level: float     # the broken swing level


@dataclass
class StructureResult:
    """Full structural read of a timeframe."""

    bias: Bias
    impulse_direction: str   # the 80% move: "up" | "down" | "flat"
    retrace_direction: str   # the 20% move: "down" | "up" | "flat"
    swings: List[SwingPoint] = field(default_factory=list)
    bos_events: List[BOSEvent] = field(default_factory=list)
    last_bos: Optional[BOSEvent] = None
    market_shift: bool = False


# ---- Supply & Demand --------------------------------------------------------


@dataclass
class SupplyDemandZone:
    """A supply (sell) or demand (buy) zone.

    origin values map to the PDF concepts:
      - "manipulative" : Bougie manipulatrice (manipulation candle)
      - "money_take"   : Bougie qui prend l'argent (candle that takes money)
      - "breaker"      : Breaker block / polarite inverse (polarity flip)
    """

    zone_type: ZoneType
    top: float
    bottom: float
    index: int
    timestamp: object
    origin: str = "manipulative"
    mitigated: bool = False          # price already reacted on this zone
    confirmed_by_fvg: bool = False   # an imbalance backs this zone


# ---- Imbalance (Fair Value Gap / IPA) --------------------------------------


@dataclass
class FairValueGap:
    """Fair Value Gap / IPA - a 3-candle price imbalance."""

    fvg_type: FVGType
    top: float
    bottom: float
    index: int
    timestamp: object
    filled: bool = False


# ---- Liquidity --------------------------------------------------------------


@dataclass
class LiquidityLevel:
    """A liquidity pool: EQL, EQH, trendline or a standalone swing level."""

    level_type: str   # "EQL" | "EQH" | "trendline" | "swing_high" | "swing_low"
    price: float
    index: int
    timestamp: object
    swept: bool = False


# ---- Signal -----------------------------------------------------------------


@dataclass
class Signal:
    """Final entry signal produced by the trigger chain."""

    signal: SignalType
    bias: Optional[Bias] = None
    filters_passed: dict = field(default_factory=dict)
    entry_top: float = 0.0
    entry_bottom: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rr_ratio: Optional[float] = None
    confidence: str = "low"   # "high" | "medium" | "low"
    zone: Optional[SupplyDemandZone] = None
    support: Optional[float] = None   # iron condor: lower bound
    resistance: Optional[float] = None  # iron condor: upper bound
    reason: str = ""
