import asyncio
from typing import Literal

import ccxt.async_support as ccxt
import src.exchanges as my_exchanges
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.deps.converter import Converter
from src.lib.schema import TickerInfo
from src.db import crud


class AllMarketsLoader:
    def __init__(self, exchange_names: list[str] | None = None):
        self.exchanges = []
        self.target = None

        if exchange_names is None:
            from ccxt import exchanges
            exchange_names = exchanges

        self.total = len(exchange_names)
        for exchange_name in exchange_names:
            exchange = getattr(ccxt, exchange_name)()

            self._init_exchange_custom_properties(exchange)
            self.exchanges.append(exchange)

        lg.info(f"Exchanges: {len(self.exchanges)}")

    async def start(self) -> None:
        lg.info("Start loading markets")
        await asyncio.gather(*[self._load_markets(exchange) for exchange in self.exchanges])
        lg.info(f"Markets loaded: {len(self.exchanges)}/{self.total}")

    async def close(self) -> None:
        lg.info("Closing markets")
        await asyncio.gather(*[exchange.close() for exchange in self.exchanges])

    def get_target_markets(self, target: Literal['ohlcv', 'volume']):
        """
            Get list of exchanges, that support target methods
        """
        self.target = target
        return self._get_target_exchanges()

    async def _load_markets(self, exchange: BaseExchange):
        for attempt in range(5):
            try:
                await exchange.load_markets()
                break
            except Exception as e:
                lg.error(f"Error markets for: {exchange}, attempt: {attempt + 1}, {str(e)[:100]}")
            await asyncio.sleep(attempt + 1)
        else:
            try:
                await exchange.close()
            except AttributeError as ae:
                lg.error(f"Cant release resources for {exchange.id}, {ae}")
            lg.info(f"{exchange.id} failed load markets :(")
            self.exchanges.remove(exchange)  # remove if markets unavailable

    def _get_target_exchanges(self) -> list[BaseExchange]:
        target_exchanges = []
        lg.debug(len(self.exchanges))

        if self.target == "ohlcv":
            for exchange in self.exchanges:
                if exchange.has["fetchOHLCV"]:
                    target_exchanges.append(exchange)

        elif self.target == "volume":
            for exchange in self.exchanges:
                # if exchange.has["fetchTickers"]:
                target_exchanges.append(exchange)

            self._remove_duplicate_exchanges(target_exchanges)
        else:
            raise ValueError(f"Unknown target: {self.target}")

        self.start_counter = len(self.exchanges)
        return target_exchanges

    def _remove_duplicate_exchanges(self, target_exchanges: list[BaseExchange]):
        """
            Some exchanges have more than 1 instance, futures accounts, etc.
        """
        lg.debug("removing duplictes")
        names = [exchange.id for exchange in target_exchanges]
        ex_list = target_exchanges[:]
        lg.debug(names)
        if 'binance' in names:
            for exchange in ex_list:
                if exchange.id in ('binanceusdm', "binancecoinm", "binanceus", "binancecoinm"):
                    target_exchanges.remove(exchange)
        if "hitbtc" in names:
            for exchange in ex_list:
                if exchange.id == 'hitbtc3':
                    target_exchanges.remove(exchange)
        if "kraken" in names:
            for exchange in ex_list:
                if exchange.id == 'krakenfutures':
                    target_exchanges.remove(exchange)
        if "poloniex" in names:
            for exchange in ex_list:
                if exchange.id == 'poloniexfutures':
                    target_exchanges.remove(exchange)
        if "bitfinex" in names:
            for exchange in ex_list:
                if exchange.id == 'bitfinex2':
                    target_exchanges.remove(exchange)
        if "coinbasepro" in names:
            for exchange in ex_list:
                if exchange.id == 'coinbase':
                    target_exchanges.remove(exchange)
        if "htx" in names:
            for exchange in ex_list:
                if exchange.id == 'huobi':
                    target_exchanges.remove(exchange)
        if "gate" in names:
            for exchange in ex_list:
                if exchange.id == 'gateio':
                    target_exchanges.remove(exchange)
        if "kucoin" in names:
            for exchange in ex_list:
                if exchange.id == 'kucoinfutures':
                    target_exchanges.remove(exchange)

        names = [exchange.id for exchange in target_exchanges]
        lg.debug(names)

    def _init_exchange_custom_properties(self, exchange: BaseExchange):
        exchange.enableRateLimit = True
        if exchange.id == 'alpaca':
            exchange.api_key = 'PK8KJ8UDRPSC2KSGWT0J'
            exchange.secret = 'vrISGaZZCpsnA4TU31gvQ75DukxeGXeow4sIF2DS'

        if exchange.id == 'bitmart':
            exchange.fetch_timeout = 2
        else:
            exchange.fetch_timeout = 0.3


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
        try:
            self.exchange = getattr(ccxt, self.exchange_name)()
        except AttributeError:
            try:
                self.exchange = getattr(my_exchanges, self.exchange_name)()
            except AttributeError:
                raise AttributeError(f"{self.exchange_name} not supported")

        self._init_fetch_timeout()
        await self._load_markets()

        self.converter = Converter(exchange=self.exchange)
        async with AsyncSessionFactory() as session:
            await self.converter.init_converter(session=session)
        lg.info(f"{self.exchange.id} Initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            lg.info(f"{self.exchange.id} Closed")
            await self.exchange.close()

    async def _load_markets(self) -> bool:
        """Load all market data from exchange"""
        for attempt in range(3):
            try:
                await self.exchange.load_markets()
                break
            except Exception as e:
                lg.warning(f"Error markets for: {self.exchange.id}, attempt: {attempt + 1}, {str(e)[:100]}")
            await asyncio.sleep(attempt + 1)
        else:
            await self.exchange.close()
            lg.error(f"{self.exchange.id} failed load markets :(")

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
                lg.warning(str(e)[:30])
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
        for symbol, prop in self.exchange.markets.items():
            if ":" in symbol or "/" not in symbol:  # ':' and no '/' only in derivative symbol, skip it
                continue
            symbols.add(symbol)
        return symbols

    def _init_fetch_timeout(self):
        if self.exchange.id == 'bitmart':
            self.exchange.fetch_timeout = 2
        else:
            self.exchange.fetch_timeout = 0.3

    async def save_tickers(self, tickers: list[TickerInfo]) -> None:
        async with AsyncSessionFactory() as session:
            await crud.save_tickers(session=session, tickers=tickers)
