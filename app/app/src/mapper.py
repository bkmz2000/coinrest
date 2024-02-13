from contextlib import suppress

import ccxt.pro
from asyncio import run
from loguru import logger as lg
from ccxt.async_support.base.exchange import BaseExchange
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from src.lib.client import fetch_data_from_hodler
from src.lib.utils import GeckoMarkets, BaseMapper
from src.db.crud import set_mapper_data, get_mapper_data, get_exchange_cg_ids


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
        ids[market['symbol']] = market['cg_id']
    return ids



async def update_mapper(exchanges: list[BaseExchange], session: AsyncSession) -> dict[str, list[GeckoMarkets]]:
    lg.info("Updating mapper")
    mapper = defaultdict(list)

    coins = await fetch_data_from_hodler()

    total_counter = 0
    success_counter = 0

    pairs = set()  # Уникальные торговые пары
    ex_pairs = dict()  # Торговые пары для конкретной биржи

    for exchange in exchanges:
        tickers = await _find_exchange_USDT_tickers(exchange, pairs, ex_pairs)
        try:
            result = await exchange.fetch_tickers()
            for usdt_ticker in tickers:
                ticker = result.get(usdt_ticker, {})
                if not ticker or not ticker.get("last"):
                    continue
                data = {
                    "symbol": exchange.markets[ticker["symbol"]]["base"],
                    "value": ticker.get("last")
                }
                total_counter += 1
                cg_id = match_id(coins, data)
                if cg_id:
                    mapper = BaseMapper(cg_id=cg_id, exchange=exchange.id, symbol=ticker["symbol"])
                    await set_mapper_data(session=session, mapper=mapper)
                    # mapper[cg_id].append(GeckoMarkets(symbol=ticker["symbol"], exchange=exchange))
                    success_counter += 1
                lg.info(f"{total_counter}/{success_counter}, {data}")
        except Exception as e:
            lg.error(f"{exchange.id} - {e}")

    lg.info(f"Number of currencies: {len(pairs)}")
    # lg.info(f"Uniques: {pairs}")
    return mapper


async def _find_exchange_USDT_tickers(ex, pairs, ex_pairs) -> list[str]:
    """
        Для биржи находим все торговые пары {ticker}/USDT
    """
    ex_pairs[ex.id] = []
    for market in ex.markets:
        left = market.split(":")[0]
        left = left.strip()
        if left.endswith("/USDT"):
            pairs.add(left)
            ex_pairs[ex.id].append(left)
            # if left not in pairs:
    ex_pairs[ex.id] = list(set(ex_pairs[ex.id]))
    lg.info(f"{ex.id}: {len(ex_pairs[ex.id])}")
    return ex_pairs[ex.id]


def match_id(coins: list, item: dict):
    exchange_symbol = item.get("symbol")

    for coin in coins:
        if coin["symbol"] == exchange_symbol:
            if 0.95 <= coin["quote"]["USD"]["price"] / item["value"] <= 1.05:
                return coin["cgid"]

async def main():
    from src.deps.markets import AllMarketsLoader
    # exs = AllMarketsLoader(ccxt.exchanges)
    exs = AllMarketsLoader(['binance', 'mexc'])
    ex_markets = await exs.start()
    mapper = await get_mapper(ex_markets)
    print(mapper)
    await exs.close()



if __name__ == '__main__':
    run(main())
