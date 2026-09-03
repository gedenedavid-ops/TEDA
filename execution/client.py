"""
Alpaca broker client wrapper.

Thin layer over alpaca-py exposing the operations the agent needs:
account, positions, option contracts, order submission.
"""

from __future__ import annotations

from typing import List, Optional

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.trading.models import (
    OptionContract,
    Order,
    Position,
    TradeAccount,
)
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    MarketOrderRequest,
    OrderRequest,
)

from config.settings import settings


class BrokerClient:
    """Wraps the Alpaca trading + historical data clients."""

    def __init__(self) -> None:
        if not settings.alpaca_configured:
            raise RuntimeError(
                "Alpaca keys missing. Set ALPACA_API_KEY and ALPACA_SECRET_KEY "
                "in config/.env (see config/.env.example)."
            )
        self.trading = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.paper,
        )
        self.stock_data = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
        )

    # ---- Account & positions --------------------------------------------

    def get_account(self) -> TradeAccount:
        return self.trading.get_account()

    def get_positions(self) -> List[Position]:
        return self.trading.get_all_positions()

    def get_equity(self) -> float:
        return float(self.get_account().equity)

    # ---- Options ---------------------------------------------------------

    def get_option_contracts(
        self,
        underlying: str,
        contract_type: Optional[str] = None,
        expiration_date: Optional[str] = None,
        strike_min: Optional[float] = None,
        strike_max: Optional[float] = None,
        limit: int = 500,
    ) -> List[OptionContract]:
        request = GetOptionContractsRequest(
            underlying_symbols=[underlying],
            type=contract_type,
            expiration_date=expiration_date,
            strike_price_gte=str(strike_min) if strike_min is not None else None,
            strike_price_lte=str(strike_max) if strike_max is not None else None,
            limit=limit,
        )
        result = self.trading.get_option_contracts(request)
        return result.option_contracts or []

    # ---- Orders ----------------------------------------------------------

    def submit_order(self, order: OrderRequest) -> Order:
        return self.trading.submit_order(order)

    def submit_market_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        time_in_force: str = "day",
    ) -> Order:
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=time_in_force,
        )
        return self.trading.submit_order(order)

    def get_orders(self, status: str = "open", limit: int = 50) -> List[Order]:
        from alpaca.trading.requests import GetOrdersRequest

        return self.trading.get_orders(
            GetOrdersRequest(status=status, limit=limit)
        )
