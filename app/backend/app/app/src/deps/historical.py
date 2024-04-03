import asyncio
from collections import defaultdict
from dataclasses import dataclass
import random

import ccxt.async_support as ccxt
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.connection import AsyncSessionFactory
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg
from src.db.crud import get_exchange_mapper
from src.lib.utils import Match


class HistoricalMarkets:
    def __init__(self, exchange_names: list[str] | None = None):
        self.mapper = HistoricalMapper()
        # self.exchanges = []
        self.exchanges = {}
        # self.exchanges_matched = {}
        self.total = 0

        if exchange_names is None:
            from ccxt import exchanges
            exchange_names = exchanges

        for exchange_name in exchange_names:
            exchange: BaseExchange = getattr(ccxt, exchange_name)()
            if exchange.has["fetchOHLCV"]:
                self.exchanges[exchange.id] = exchange
                # self.exchanges.append(exchange)
                self.total += 1

    async def load_markets(self, session: AsyncSession):
        lg.info("Start loading markets")
        await asyncio.gather(*[self._load_markets(exchange) for exchange in self.exchanges.values()])
        lg.info(f"Historical markets loaded: {len(self.exchanges)}/{self.total}")
        await self.mapper.load_mapper(exchanges=self.exchanges, session=session)

    async def _load_markets(self, exchange: BaseExchange):
        """Load all market data from exchange"""
        for attempt in range(3):
            try:
                await exchange.load_markets()
                break
            except Exception as e:
                ...
                # lg.warning(f"Error markets for: {exchange.id}, attempt: {attempt + 1}, {str(e)[:100]}")
            await asyncio.sleep(attempt + 1)
        else:
            await self._close_markets(exchange)
            lg.error(f"{exchange.id} failed load markets :(")
            del self.exchanges[exchange.id]  # remove if markets unavailable

    async def close_markets(self) -> None:
        lg.info("Closing markets")
        await asyncio.gather(*[self._close_markets(exchange) for exchange in self.exchanges.values()])

    async def _close_markets(self, exchange: BaseExchange):
        if isinstance(exchange, BaseExchange):
            try:
                await exchange.close()
            except Exception as e:
                lg.warning(f"{exchange.id} trouble with closing: {e}")


class HistoricalMapper:
    def __init__(self) -> None:
        self.mapper = defaultdict(list)

    async def load_mapper(self, session: AsyncSession, exchanges: dict[str, BaseExchange]):
        db_mapped = await get_exchange_mapper(session=session, exchange_ids=list(exchanges.keys()))
        for exchange in db_mapped:
            self.mapper[exchange.cg_id].append(
                Match(
                    cg_id=exchange.cg_id,
                    exchange=exchanges[exchange.ccxt_name],
                    symbol=exchange.symbol
                      )
            )
        return self.mapper

    def __getitem__(self, item: str) -> list[Match] | None:
        mapped_markets = self.mapper.get(item)
        if item == "tether":
            return mapped_markets
        if mapped_markets and len(mapped_markets) > 6:
            mapped_markets = random.sample(mapped_markets, k=6)
        elif mapped_markets and len(mapped_markets) < 3:
            return None
        return mapped_markets


async def main():
    markets = HistoricalMarkets(exchange_names=['binance', 'mexc'])
    async with AsyncSessionFactory() as session:
        await markets.load_markets(session=session)
    print(markets.mapper['bitcoin'])
    await markets.close_markets()


if __name__ == "__main__":
    asyncio.run(main())
