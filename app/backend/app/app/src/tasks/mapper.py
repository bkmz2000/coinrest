from asyncio import run
from loguru import logger as lg
from ccxt.async_support.base.exchange import BaseExchange
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.connection import AsyncSessionFactory
from src.lib.client import fetch_data_from_hodler
from src.lib.utils import GeckoMarkets
from src.lib.schema import TickerToMatch, TickerMatched
from src.db import crud


async def get_mapper(exchanges: list[BaseExchange], session: AsyncSession) -> dict[str, list[GeckoMarkets]]:
    lg.info(f"Loading mapper from database")
    data = await crud.get_mapper_data(session=session)
    mapper = defaultdict(list)
    for market in data:
        for exchange in exchanges:
            if exchange.id == market.exchange:
                mapper[market.cg_id].append(GeckoMarkets(symbol=market.symbol, exchange=exchange))
                break
    # for k, v in mapper.items():
    #     lg.info(f"{k}: mapped {len(v)} exchanges")
    return mapper


async def get_cg_ids(session: AsyncSession, exchange_id: str):
    ids = {}
    cg_ids = await crud.get_exchange_cg_ids(session=session, exchange_id=exchange_id)
    for market in cg_ids:
        base = market['symbol'].split("/")[0]
        ids[base] = market['cg_id']
    lg.debug(f"{exchange_id} coingecko_ids: {ids}")
    return ids


async def update_mapper():
    """
        Updates tickers/coingecko ids for all exchanges for all tickers
    :return:
    """
    lg.info("Updating mapper")
    coins = await fetch_data_from_hodler()
    matched = []
    async with AsyncSessionFactory() as session:
        db_tickers = await crud.get_db_tickers(session=session)
        for ticker in db_tickers:
            matched_ticker = match(coins, ticker)
            if matched_ticker:
                matched.append(matched_ticker)
        lg.info(f"Matched tickers: {len(matched)}/{len(db_tickers)}")
        await crud.save_matched_tickers(session=session, tickers=matched)


def match(coins: list, ticker: TickerToMatch) -> TickerMatched | None:
    """
        Match symbol with current price to coingecko_id
    :param coins: coingecko ids with actual prices
    :param ticker: ticker from db, we try to match
    :return: Matched ticker to coingecko id or None
    """
    for coin in coins:
        if coin["symbol"] == ticker.base:
            if 0.85 <= coin["quote"]["USD"]["price"] / ticker.price_usd <= 1.15:
                return TickerMatched(id=ticker.id, base_cg=coin["cgid"])


async def main():
    await update_mapper()



if __name__ == '__main__':
    run(main())
