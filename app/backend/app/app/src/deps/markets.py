import asyncio
import os
from datetime import datetime
from typing import Literal

import ccxt.async_support as ccxt
import src.exchanges as my_exchanges
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.deps.converter import Converter
from src.lib.utils import UpdateEventTo, NotActiveExchange
from src.lib.schema import TickerInfo
from src.strapi_sync.strapi import update_strapi_state
from src.db import crud


IS_DEV = os.environ.get("IS_DEV", False)

important_field = {
    "map": 'last',
    "vol": 'baseVolume'
}


class Market:
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.exchange = None
        self.converter: Converter = None
        self.fetch_timeout = None

    async def __aenter__(self):
        # Load exchange class
        try:
            self.exchange = getattr(ccxt, self.exchange_name)()
        except AttributeError:
            try:
                self.exchange = getattr(my_exchanges, self.exchange_name)()
            except AttributeError:
                raise AttributeError(f"{self.exchange_name} not supported")

        # Check exchange is_actual, if not raise
        async with AsyncSessionFactory() as session:
            ex_crud = ExchangeCRUD()
            is_active = await ex_crud.check_is_active(session, self.exchange_name)
            if not is_active:
                raise NotActiveExchange(f"{self.exchange_name} Exchange was disabled")

            # Load markets for all exchanges
            self._init_fetch_timeout()
            await self._load_markets()

            # Init converter
            self.converter = Converter(exchange=self.exchange)
            await self.converter.init_converter(session=session)
            lg.info(f"{self.exchange.id} Initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exchange.close()
        lg.info(f"{self.exchange.id} Closed")


    async def _load_markets(self) -> bool:
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


    async def fetch_all_tickers(self, symbols: set, target: Literal['map', 'vol'] = 'map') -> dict:
        """
        Fetch tickers with 3 steps:
             1. Try to fetch ALL tickers with 1 request
             2*. If not all tickers were returned, or some of them with null volume,
             try to fetch tickers as batch
             3*. If some tickers still not returned, try to fetch them one by one
        :param target: Purpose of func executing. For mapping(map) important field in ticker -> 'last',
        for volume counting(vol) -> 'volume'
        :param symbols: unique trading pairs without derivatives
        :return: tickers
        """
        result = {}
        returned = 0
        target = important_field.get(target)
        for i in range(3):
            # Fetch all tickers
            try:
                tickers = await self.exchange.fetch_tickers()
                result.update(tickers)

                # lg.debug(len(tickers))
                for symbol, prop in tickers.items():
                    field = prop.get(target)
                    if symbol in symbols:
                        symbols.remove(symbol)  # Remove if symbol present in tickers...
                    if field is None:  # ...But return if field is None, so we'll request it below
                        if ":" in symbol or "/" not in symbol:
                            continue
                        returned += 1
                        symbols.add(symbol)
                break
            except Exception as e:
                lg.warning(str(e)[:100])
                await asyncio.sleep(0.5)

        if not symbols:
            return result

        lg.debug(f"{self.exchange.id} has {len(symbols)} not in tickers, returned: {returned}")
        # If some symbol not in tickers, try to fetch them as a batch
        l_symbols = list(symbols)
        batch = 50
        for i in range(0, len(symbols), batch):
            await asyncio.sleep(self.exchange.fetch_timeout)
            try:
                # lg.debug(f"{ex.id}: {l_symbols[i:i + batch][:10]}, {i}, {i + batch}")
                tickers = await self.exchange.fetch_tickers(symbols=l_symbols[i:i + batch])
                result.update(tickers)

                for symbol, prop in tickers.items():
                    field = prop.get(target)
                    if symbol in symbols:
                        symbols.remove(symbol)  # Remove if symbol present in tickers...
                    if field is None:  # ...But return if field is None, so we'll request it below
                        if ":" in symbol or "/" not in symbol:
                            continue
                        returned += 1
                        symbols.add(symbol)
            except Exception as e:
                lg.warning(str(e)[:30])
        if not symbols:
            return result

        lg.debug(f"{self.exchange.id} has {len(symbols)} to fetch by one")
        # If some symbol not in tickers, try to fetch them one by one
        for symbol in symbols:
            if ":" in symbol or "/" not in symbol:
                continue
            await asyncio.sleep(self.exchange.fetch_timeout)
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                result[symbol] = ticker
            except Exception as e:
                pass  # too many logs
                # if "delisted" in str(e):
                #     continue
                # lg.warning(f"{symbol}: {e}")
        return result

    def get_all_market_symbols(self) -> set:
        """
            Get all market trading pairs(symbols) without derivatives
        """
        symbols = set()
        if not self.exchange.markets:
            return symbols
        for symbol, prop in self.exchange.markets.items():
            if ":" in symbol or "/" not in symbol:  # ':' and no '/' only in derivative symbol, skip it
                continue
            symbols.add(symbol)
        return symbols

    def _init_fetch_timeout(self):
        if self.exchange.id == 'bitmart':
            self.exchange.fetch_timeout = 2
        elif self.exchange.id == 'ascendex':
            self.exchange.fetch_timeout = 5
        else:
            self.exchange.fetch_timeout = 0.3

    async def save_tickers(self, tickers: list[TickerInfo]) -> None:
        if tickers:
            async with AsyncSessionFactory() as session:
                await crud.save_tickers(session=session, tickers=tickers)
            if IS_DEV:
                return
            event = UpdateEventTo(ticker_num=len(tickers), last_update=str(datetime.now()))
            await update_strapi_state(self.exchange.id, event)
