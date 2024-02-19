from asyncio import run
from loguru import logger as lg
from ccxt.async_support.base.exchange import BaseExchange
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from src.deps.markets import AllMarketsLoader
from src.lib.client import fetch_data_from_hodler
from src.lib.utils import GeckoMarkets, BaseMapper
from src.deps.converter import Converter
from src.db.crud import set_mapper_data, get_mapper_data, get_exchange_cg_ids
from src.tasks.methods import get_all_market_symbols, fetch_all_tickers


async def get_mapper(exchanges: list[BaseExchange], session: AsyncSession) -> dict[str, list[GeckoMarkets]]:
    lg.info(f"Loading mapper from database")
    data = await get_mapper_data(session=session)
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
    cg_ids = await get_exchange_cg_ids(session=session, exchange_id=exchange_id)
    for market in cg_ids:
        base = market['symbol'].split("/")[0]
        ids[base] = market['cg_id']
    lg.debug(f"{exchange_id} coingecko_ids: {ids}")
    return ids



async def update_mapper(exchanges: list[BaseExchange]):
    lg.info("Updating mapper")
    coins = await fetch_data_from_hodler()
    # coins = []

    for exchange in exchanges:
        try:
            async with Converter(exchange=exchange, geckos=coins) as converter:
                symbols = get_all_market_symbols(exchange)
                tickers = await fetch_all_tickers(ex=exchange, symbols=symbols)
                for symbol, prop in tickers.items():
                    # lg.info(f"{symbol}: {prop}")
                    last_price = prop.get("last")
                    await converter.match_and_save(symbol, price=last_price)
        except Exception as e:
            lg.error(f"{exchange.id} - {e}")


def match_id(coins: list, item: dict):
    exchange_symbol = item.get("symbol")

    for coin in coins:
        if coin["symbol"] == exchange_symbol:
            if 0.95 <= coin["quote"]["USD"]["price"] / item["value"] <= 1.05:
                return coin["cgid"]


async def main():
    exs = AllMarketsLoader()
    await exs.start()
    ex_markets = exs.get_target_markets(target="volume")
    await update_mapper(ex_markets)
    await exs.close()



if __name__ == '__main__':
    run(main())
