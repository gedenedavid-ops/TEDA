"""
Application configuration loaded from environment variables.

Copy config/.env.example -> config/.env and fill in your keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (trade/.env) regardless of the cwd.
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)


@dataclass
class Settings:
    # Alpaca
    alpaca_api_key: str
    alpaca_secret_key: str
    paper: bool = True

    # Featherless (OpenAI-compatible endpoint)
    featherless_api_key: str = ""
    featherless_base_url: str = "https://api.featherless.ai/v1"
    featherless_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # Risk (SMV rules)
    risk_per_trade_pct: float = 0.01   # 1% max per trade
    min_rr_ratio: float = 7.0          # 1:7 minimum risk/reward
    max_position_pct: float = 0.25     # max 25% of equity per position

    # Timeframes (SMV pairs)
    htf_timeframe: str = "1D"          # structure / 80-20 rule
    zone_timeframe: str = "4H"         # supply/demand zones
    ltf_timeframe: str = "1H"          # imbalance + liquidity + market shift
    trigger_timeframe: str = "15Min"   # optional precise trigger

    # Options
    default_dte_min: int = 7
    default_dte_max: int = 45

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            alpaca_api_key=os.getenv("ALPACA_API_KEY", ""),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", ""),
            featherless_api_key=os.getenv("FEATHERLESS_API_KEY", ""),
            featherless_base_url=os.getenv(
                "FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"
            ),
            featherless_model=os.getenv(
                "FEATHERLESS_MODEL", "Qwen/Qwen2.5-7B-Instruct"
            ),
        )

    @property
    def alpaca_configured(self) -> bool:
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

    @property
    def featherless_configured(self) -> bool:
        return bool(self.featherless_api_key)


settings = Settings.from_env()
