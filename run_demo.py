"""
Smoke-test / demo for the SMV strategy engine.

Generates synthetic OHLCV data (a bullish trend with retracements)
and runs the full detection chain, printing the outputs so we can
visually verify each module before wiring it to Alpaca.

Run:  python run_demo.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategy import imbalance, liquidity, structure, supply_demand, triggers
from strategy.models import StructureResult


def synthetic_ohlcv(n: int = 500, seed: int = 7) -> pd.DataFrame:
    """A random walk with an upward drift and occasional sharp impulses."""
    rng = np.random.default_rng(seed)
    base = 100.0
    closes = [base]
    for i in range(1, n):
        drift = 0.06
        shock = rng.normal(0, 0.35)
        closes.append(closes[-1] + drift + shock)

    closes = np.array(closes)
    opens = np.roll(closes, 1)
    opens[0] = closes[0] - 0.1

    highs = np.maximum(opens, closes) + np.abs(rng.normal(0, 0.2, n))
    lows = np.minimum(opens, closes) - np.abs(rng.normal(0, 0.2, n))

    index = pd.date_range("2026-01-01", periods=n, freq="1h")
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes}, index=index
    )


def main() -> None:
    df_htf = synthetic_ohlcv(500, seed=7)
    df_ltf = synthetic_ohlcv(500, seed=13)

    print("=" * 60)
    print("STRUCTURE (HTF)")
    print("=" * 60)
    s: StructureResult = structure.analyze_structure(df_htf, lookback=5)
    print(f"bias          = {s.bias}")
    print(f"impulse/retrace = {s.impulse_direction} / {s.retrace_direction}")
    print(f"swings        = {len(s.swings)}")
    print(f"bos events    = {len(s.bos_events)}")
    if s.last_bos:
        print(f"last bos      = {s.last_bos.kind} ({s.last_bos.bos_type}) @ {s.last_bos.level:.2f}")

    print()
    print("=" * 60)
    print("SUPPLY & DEMAND")
    print("=" * 60)
    zones = supply_demand.detect_zones(df_ltf)
    supply_demand.mark_mitigated(df_ltf, zones)
    breakers = supply_demand.detect_breaker_blocks(df_ltf, zones)
    print(f"zones         = {len(zones)}")
    print(f"breakers      = {len(breakers)}")
    for z in zones[:5]:
        print(
            f"  {z.zone_type:6s} {z.bottom:.2f}-{z.top:.2f} "
            f"mitigated={z.mitigated} origin={z.origin}"
        )

    print()
    print("=" * 60)
    print("IMBALANCE (FVG)")
    print("=" * 60)
    fvgs = imbalance.analyze_imbalance(df_ltf)
    print(f"fvgs          = {len(fvgs)}")
    unfilled = [f for f in fvgs if not f.filled]
    print(f"unfilled      = {len(unfilled)}")
    for f in fvgs[:5]:
        print(
            f"  {f.fvg_type:8s} {f.bottom:.2f}-{f.top:.2f} filled={f.filled}"
        )

    print()
    print("=" * 60)
    print("LIQUIDITY")
    print("=" * 60)
    levels = liquidity.analyze_liquidity(df_ltf, lookback=5)
    print(f"levels        = {len(levels)}")
    swept = [l for l in levels if l.swept]
    print(f"swept         = {len(swept)}")
    for l in levels[:5]:
        print(f"  {l.level_type:10s} {l.price:.2f} swept={l.swept}")

    print()
    print("=" * 60)
    print("TRIGGER CHAIN")
    print("=" * 60)
    current = float(df_ltf["close"].iloc[-1])
    sig = triggers.evaluate_trigger(
        structure_htf=s,
        zones=zones + breakers,
        fvgs=fvgs,
        liquidity=levels,
        df_ltf=df_ltf,
        current_price=current,
    )
    print(f"signal        = {sig.signal}")
    print(f"bias          = {sig.bias}")
    print(f"confidence    = {sig.confidence}")
    print(f"filters       = {sig.filters_passed}")
    print(f"entry         = {sig.entry_bottom:.2f} - {sig.entry_top:.2f}")
    print(f"SL            = {sig.stop_loss}")
    print(f"TP            = {sig.take_profit}")
    print(f"RR            = {sig.rr_ratio}")
    print(f"reason        = {sig.reason}")


if __name__ == "__main__":
    main()
