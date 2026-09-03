"""
Market data helpers: fetch OHLCV bars from Alpaca and convert them into
the pandas DataFrame format expected by the strategy modules.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# Map friendly timeframe strings -> TimeFrame objects.
TIMEFRAME_MAP = {
    "1D": TimeFrame.Day,
    "4H": TimeFrame(4, TimeFrameUnit.Hour),
    "1H": TimeFrame.Hour,
    "15Min": TimeFrame(15, TimeFrameUnit.Minute),
    "5Min": TimeFrame(5, TimeFrameUnit.Minute),
}


def parse_timeframe(value: str) -> TimeFrame:
    """Convert a config string ('1D', '4H', '15Min') to a TimeFrame."""
    if value not in TIMEFRAME_MAP:
        raise ValueError(f"Unknown timeframe '{value}'. Use one of {list(TIMEFRAME_MAP)}")
    return TIMEFRAME_MAP[value]


def bars_to_dataframe(bars) -> pd.DataFrame:
    """Convert Alpaca Bar objects into an OHLCV DataFrame."""
    records = [
        {
            "timestamp": b.timestamp,
            "open": float(b.open),
            "high": float(b.high),
            "low": float(b.low),
            "close": float(b.close),
            "volume": float(b.volume),
        }
        for b in bars
    ]
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.set_index("timestamp")


# Approximate seconds per bar unit, used to compute the lookback window.
_UNIT_SECONDS = {
    TimeFrameUnit.Minute: 60,
    TimeFrameUnit.Hour: 3600,
    TimeFrameUnit.Day: 86400,
    TimeFrameUnit.Week: 604800,
    TimeFrameUnit.Month: 2592000,
}


def _lookback_delta(tf: TimeFrame, limit: int) -> timedelta:
    """Estimate a calendar lookback window that yields ~limit bars.

    Adds a buffer to account for weekends (daily) and overnight gaps
    (intraday), since Alpaca only returns bars during market hours.
    """
    unit_seconds = _UNIT_SECONDS.get(tf.unit, 86400)
    span_seconds = unit_seconds * tf.amount * limit
    buffer = 2.5 if tf.unit == TimeFrameUnit.Day else 1.5
    return timedelta(seconds=span_seconds * buffer)


def fetch_stock_bars(
    client: StockHistoricalDataClient,
    symbol: str,
    timeframe: str,
    limit: int = 500,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    feed: DataFeed = DataFeed.IEX,
) -> pd.DataFrame:
    """Fetch historical OHLCV bars for a stock/ETF and return a DataFrame.

    Defaults to the free IEX feed (paper accounts without a SIP
    subscription cannot query SIP data).
    """
    tf = parse_timeframe(timeframe)
    if end is None:
        end = datetime.now(timezone.utc)
    if start is None:
        start = end - _lookback_delta(tf, limit)

    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=tf,
        start=start,
        end=end,
        feed=feed,
    )
    result = client.get_stock_bars(request)
    bars = result.data.get(symbol, [])
    return bars_to_dataframe(bars)


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample an OHLCV DataFrame to a coarser rule (e.g. '4h', '1D')."""
    return (
        df.resample(rule)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
    )
