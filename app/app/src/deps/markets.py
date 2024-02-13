import asyncio
from typing import Literal

import ccxt.async_support as ccxt
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


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
            exchange.enableRateLimit = True
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
            await asyncio.sleep(attempt+1)
        else:
            try:
                await exchange.close()
            except AttributeError as ae:
                lg.error(f"Cant release resources for {exchange.id}, {ae}")
            lg.info(f"{exchange.id} failed load markets :(")
            self.exchanges.remove(exchange)  # remove if markets unavailable

    def _get_target_exchanges(self) -> list[BaseExchange]:
        target_exchanges = []
        lg.debug("sorting target exchanges")
        lg.debug(len(self.exchanges))

        if self.target == "ohlcv":
            for exchange in self.exchanges:
                if exchange.has["fetchOHLCV"]:
                    target_exchanges.append(exchange)

        elif self.target == "volume":
            for exchange in self.exchanges:
                if exchange.has["fetchTickers"]:
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
        if "kucoin" in names:
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
        if "coinbase" in names:
            for exchange in ex_list:
                if exchange.id == 'coinbasepro':
                    target_exchanges.remove(exchange)
        if "htx" in names:
            for exchange in ex_list:
                if exchange.id == 'huobi':
                    target_exchanges.remove(exchange)
        if "gate" in names:
            for exchange in ex_list:
                if exchange.id == 'gateio':
                    target_exchanges.remove(exchange)

        names = [exchange.id for exchange in target_exchanges]
        lg.debug(names)