import asyncio
import sys
import time

import ccxt.async_support as ccxt
from ccxt.async_support.base.exchange import BaseExchange
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.connection import AsyncSessionFactory

from src.db.crud import get_coins_from_db
from src.lib import utils
from collections.abc import Iterable

frames = {
    "5m": 288,
    "1h": 840,
    "1d": 1000,
}

# lg.add(sys.stdout, level="INFO")

async def fetch_markets_chart(exchanges: list[utils.GeckoMarkets],
                              currency: str,
                              timeframe: str) -> dict[str, list[tuple[int, int]]] | None:
    result = await fetch_all_ohlcv(exchanges, timeframe)
    return result


async def fetch_all_ohlcv(exchanges: list[utils.GeckoMarkets], timeframe: str) -> dict[str, list[tuple[int, int]]] | None:
    tasks = [asyncio.create_task(fetch_ohlcv_loop(exchange.exchange, exchange.symbol, timeframe))
             for exchange in exchanges]
    result = await _get_first_task(tasks)
    return result


async def fetch_ohlcv_loop(exchange: BaseExchange, symbol: str, timeframe: str) -> dict[str, list[tuple[int, float]]]:
    limit = frames[timeframe]
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    if len(ohlcv) < int(limit) and timeframe != "1d":
        raise Exception("Not enough data")
    _check_fresh(ohlcv, timeframe)
    if timeframe == "1d":
        return {"prices": [tuple((_trunc_time(item[0]), item[4])) for item in ohlcv],
                "exchange": exchange.id}

    result = {"prices": [tuple((item[0], item[4])) for item in ohlcv],
              "exchange": exchange.id}
    return result


async def _get_first_task(tasks: Iterable[asyncio.Task]) -> dict[str, list[tuple[int, int]]] | None:
    if not tasks:
        return None
    result: list[tuple[int, int]] | None = None

    # Fetch all exchanges in parallel
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
        timeout=5
    )

    # Get the first result
    for task in done:
        exception = task.exception()
        if exception is None:
            result = task.result()
            break

    gather = asyncio.gather(*pending, return_exceptions=True)

    if not done or result:  # If first result is not exception,
        gather.cancel()  # or cancelled due to timeout - cancel other tasks
    elif pending:
        result = await _get_first_task(pending)  # Wait the next task if previous is None
    else:
        return None  # If no more pending tasks

    try:
        await gather
    except asyncio.CancelledError:
        pass

    return result


def _check_fresh(ohlcv: list, timeframe: str) -> None:
    """
        Check if the values received from exchange are actual
    """
    if timeframe == "5m":
        stmp = ohlcv[-1][0] // 1000
        now = int(time.time())
        diff = now - stmp
        if diff > 900:  # more 15 minutes
            raise Exception("Too old values")

    elif timeframe == "1h":
        stmp = ohlcv[-1][0] // 1000
        now = int(time.time())
        diff = now - stmp
        if diff > 7_200:  # more 2 hours
            raise Exception("Too old values")

    elif timeframe == "1d":
        stmp = ohlcv[-1][0] // 1000
        now = int(time.time())
        diff = now - stmp
        if diff > 172_800:  # more 2 days
            raise Exception("Too old values")


async def get_coins(session: AsyncSession):
    coins = await get_coins_from_db(session=session)
    result = {}
    for coin in coins:
        result[coin.cg_id] = utils.CoinResponse(usd=coin.price, usd_24h_vol=coin.volume)
    return result



async def main():
    from src.deps.markets import AllMarketsLoader

    exs = AllMarketsLoader(exchange_names=["binance"])
    # exs = AllMarketsLoader()
    await exs.start()
    exchanges = exs.get_target_markets(target="volume")
    # await asyncio.gather(*[get_price_and_volume(ex=ex) for ex in exchanges])
    await exs.close()


def _trunc_time(timestamp: int):
    """
        Strict all timestamps to 00.00.00 (hh.mm.ss)
    """
    trunc = timestamp % 86_400_000
    return timestamp - trunc


if __name__ == '__main__':
    asyncio.run(main())
