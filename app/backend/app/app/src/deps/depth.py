import asyncio

import ccxt.async_support as ccxt
import src.exchanges as my_exchanges
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_ticker import TickerCRUD
from ccxt.base.errors import BadSymbol, RateLimitExceeded
from src.lib import utils
from src.db import crud

depth_limits = {
    "cryptocom": 50,
    "bitopro": 50,
    "coinex": 50,
    "htx": 150,
    "kucoin": 100,
    "binance": 5000,
    "poloniex": 150,
    "coinone": 15,
}

class OrderBookMarket:
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.session = None
        self.exchange = None
        self.orderbook_coins = None
        self.depth_limit = depth_limits.get(exchange_name, 1000)

    async def __aenter__(self):
        try:
            self.exchange = getattr(ccxt, self.exchange_name)()
        except AttributeError:
            try:
                self.exchange = getattr(my_exchanges, self.exchange_name)()
            except AttributeError:
                raise AttributeError(f"{self.exchange_name} not supported")
        self.session = AsyncSessionFactory()
        await self._load_markets()
        self._init_fetch_timeout()
        lg.info(f"{self.exchange.id} OrderBook Initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exchange.close()
        await self.session.close()
        lg.info(f"{self.exchange.id} Closed")

    async def _load_markets(self):
        """Load all market data from exchange"""
        for attempt in range(3):
            try:
                await self.exchange.load_markets()
                break
            except Exception as e:
                ...  # number of attempts doesn't matter, spam only.
                # lg.warning(f"Error markets for: {self.exchange.id}, attempt: {attempt + 1}, {str(e)[:100]}")
            await asyncio.sleep(attempt + 1)
        else:
            self.exchange.markets = {}
            lg.warning(f"{self.exchange.id} failed load markets :(")

    def _init_fetch_timeout(self):
        if self.exchange.id == 'bitmart':
            self.exchange.fetch_timeout = 2
        elif self.exchange.id == 'ascendex':
            self.exchange.fetch_timeout = 5
        else:
            self.exchange.fetch_timeout = 0.3

    async def get_exchange_coins_for_orderbook(self) -> list[utils.OrderBookCoin]:
        """
            Get coins that must be fetched from specific exchange
        """
        t_crud = TickerCRUD()
        coins = await t_crud.get_exchange_coins_for_orderbook(
            session=self.session,
            exchange=self.exchange_name)
        return coins

    async def get_order_books(self, orderbook_coins: list[utils.OrderBookCoin]):
        orders = []
        for coin in orderbook_coins:
            try:
                await asyncio.sleep(self.exchange.fetch_timeout)
                result = await self.exchange.fetch_order_book(coin.symbol, limit=self.depth_limit)
                base, quote = result["symbol"].split("/")
                bids = [(bid[0], bid[1]) for bid in result["bids"]]
                asks = [(ask[0], ask[1]) for ask in result["asks"]]
                orders.append(utils.OrderBook(
                    cg_id=coin.cg_id,
                    base=base,
                    quote=quote,
                    exchange=self.exchange.id,
                    bids=bids,
                    asks=asks
                ))
            except AttributeError as ae:
                lg.warning(f"{self.exchange.id} not support order book fetching: {ae}")
                break
            except BadSymbol as e:
                lg.warning(f"Bad symbol for {self.exchange_name} {coin.cg_id}: {e}")
            except RateLimitExceeded as rle:
                lg.warning(f"Rate limit exceed {self.exchange_name} {rle}")
                await asyncio.sleep(5)
            except Exception as e:
                lg.warning(f"{self.exchange.id} fetch order book failed {coin}: {e}")
        return orders

    async def save_order_books(self, orders: list[utils.OrderBook]) -> None:
        if orders:
            await crud.save_orders(session=self.session, orders=orders)
