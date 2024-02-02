import asyncio
import ccxt.async_support as ccxt
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg

from ccxt import exchanges


class AllMarketsLoader:
    def __init__(self, exchange_names: list[str]):
        self.exchanges = []
        self.start_counter = 0
        for exchange_name in exchange_names:
            exchange = getattr(ccxt, exchange_name)()
            if exchange.has["fetchOHLCV"]:
                exchange.enableRateLimit = True
                self.start_counter += 1
                self.exchanges.append(exchange)
        lg.info(f"Exchanges support OHLCV: {self.start_counter}")

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
