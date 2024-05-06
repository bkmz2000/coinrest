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
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.lib.utils import Match


class HistoricalMarkets:
    def __init__(self, exchange_names: list[str] | None = None):
        self.mapper = HistoricalMapper()
        self.exchanges = {}
        self.trusted_exchanges = []
        # self.exchanges_matched = {}

        if exchange_names is None:
            from ccxt import exchanges
            self.exchange_names = exchanges
        else:
            self.exchange_names = exchange_names

    async def _get_trusted_exchanges(self, session: AsyncSession):
        """
            Get exchanges with trust score > 5
        """
        crud = ExchangeCRUD()
        return await crud.get_most_trusted(session=session)

    async def load_markets(self, session: AsyncSession):
        trusted_exchanges = await self._get_trusted_exchanges(session=session)
        for exchange_name in self.exchange_names:
            if exchange_name in trusted_exchanges:  # check exchange is trusted
                exchange: BaseExchange = getattr(ccxt, exchange_name)()
                if exchange.has["fetchOHLCV"]:  # check exchange can fetch historical data
                    self.exchanges[exchange.id] = exchange
        await self.mapper.load_mapper(exchanges=self.exchanges, session=session)

        lg.info("Start loading markets")
        await asyncio.gather(*[self._load_markets(exchange) for exchange in self.exchanges.values()])
        lg.info(f"Historical markets loaded: {len(self.exchanges)}/{len(trusted_exchanges)}")


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
            lg.warning(f"{exchange.id} failed load markets :(")
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
        if mapped_markets and len(mapped_markets) >= 4:
            mapped_markets = random.sample(mapped_markets, k=4)
        return mapped_markets


async def main():
    markets = HistoricalMarkets(exchange_names=['binance', 'mexc'])
    async with AsyncSessionFactory() as session:
        await markets.load_markets(session=session)
    print(markets.mapper['bitcoin'])
    await markets.close_markets()


if __name__ == "__main__":
    asyncio.run(main())
