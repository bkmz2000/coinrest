import asyncio
from typing import Literal

import ccxt.async_support as ccxt
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


class AllMarketsLoader:
    def __init__(self, target: Literal['ohlcv', 'volume'], exchange_names: list[str] | None = None):
        self.exchanges = []
        self.start_counter = 0
        self.target = target

        if exchange_names is None:
            from ccxt import exchanges
            exchange_names = exchanges

        for exchange_name in exchange_names:
            exchange = getattr(ccxt, exchange_name)()
            exchange.enableRateLimit = True
            self.exchanges.append(exchange)

        self._sort_target_exchanges()

        lg.info(f"Exchanges for {self.target}: {self.start_counter}")

    async def start(self) -> list[BaseExchange]:
        lg.info("Start loading markets")
        await asyncio.gather(*[self._load_markets(exchange) for exchange in self.exchanges])
        lg.info(f"Markets loaded: {len(self.exchanges)}/{self.start_counter}")
        return self.exchanges

    async def close(self):
        lg.info("Closing markets")
        await asyncio.gather(*[exchange.close() for exchange in self.exchanges])

    async def _load_markets(self, exchange: BaseExchange):
        for attempt in range(5):
            try:
                await exchange.load_markets()
                break
            except Exception as e:
                lg.error(f"Error markets for: {exchange}, attempt: {attempt + 1}, {str(e)[:100]}")
            await asyncio.sleep(attempt+1)
        else:
            await exchange.close()
            lg.info(f"{exchange.id} failed load markets :(")
            self.exchanges.remove(exchange)  # remove if markets unavailable

    def _sort_target_exchanges(self):
        """
            Delete from list exchanges, that do not support target methods
        """
        lg.debug("sorting target exchanges")
        lg.debug(len(self.exchanges))
        if self.target == "ohlcv":
            for exchange in self.exchanges:
                if not exchange.has["fetchOHLCV"]:
                    self.exchanges.remove(exchange)

        elif self.target == "volume":
            for exchange in self.exchanges:
                if not exchange.has["fetchTickers"]:
                    self.exchanges.remove(exchange)
            self._remove_duplicate_exchanges()

        self.start_counter = len(self.exchanges)

    def _remove_duplicate_exchanges(self):
        """
            Some exchanges have more than 1 instance, futures accounts, etc.
        """
        lg.debug("removing duplictes")
        names = [exchange.id for exchange in self.exchanges]
        ex_list = self.exchanges[:]
        lg.debug(names)
        if 'binance' in names:
            for exchange in ex_list:
                if exchange.id in ('binanceusdm', "binancecoinm", "binanceus", "binancecoinm"):
                    self.exchanges.remove(exchange)
        if "hitbtc" in names:
            for exchange in ex_list:
                if exchange.id == 'hitbtc3':
                    self.exchanges.remove(exchange)
        if "kucoin" in names:
            for exchange in ex_list:
                if exchange.id == 'krakenfutures':
                    self.exchanges.remove(exchange)
        if "poloniex" in names:
            for exchange in ex_list:
                if exchange.id == 'poloniexfutures':
                    self.exchanges.remove(exchange)
        if "bitfinex" in names:
            for exchange in ex_list:
                if exchange.id == 'bitfinex2':
                    self.exchanges.remove(exchange)
        if "coinbase" in names:
            for exchange in ex_list:
                if exchange.id == 'coinbasepro':
                    self.exchanges.remove(exchange)
        if "htx" in names:
            for exchange in ex_list:
                if exchange.id == 'huobi':
                    self.exchanges.remove(exchange)
        if "gate" in names:
            for exchange in ex_list:
                if exchange.id == 'gateio':
                    self.exchanges.remove(exchange)