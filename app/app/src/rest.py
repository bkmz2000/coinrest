import asyncio
import time
from typing import NoReturn

import ccxt.async_support as ccxt
from ccxt.async_support.base.exchange import BaseExchange
from src.lib.utlis import GeckoMarkets
from loguru import logger as lg
from starlette.exceptions import HTTPException
from collections.abc import Iterable

async def fecth_markets_chart(exchanges: list[GeckoMarkets],
                              currency: str,
                              timeframe: str) -> list[tuple[int, int]] | None:
    result = await fetch_all_ohlcv(exchanges, timeframe)
    return result


async def fetch_all_ohlcv(exchanges: list[GeckoMarkets], timeframe: str) -> list[tuple[int, int]] | None:
    tasks = [asyncio.create_task(fetch_ohlcv_loop(exchange.exchange, exchange.symbol, timeframe))
             for exchange in exchanges]
    result = await _get_first_task(tasks)
    return result


async def _get_first_task(tasks: Iterable[asyncio.Task]) -> list[tuple[int, int]] | None:
    if not tasks:
        return None
    result: list[tuple[int, int]] | None = None

    # Fetch all exchanges in parallel
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
        timeout=2
    )

    # Get the first result
    for task in done:
        exception = task.exception()
        if exception is None:
            result = task.result()
            break

    gather = asyncio.gather(*pending, return_exceptions=True)

    if not done or result:  # If first result is not exception,
        gather.cancel()     # or cancelled due to timeout - cancel other tasks
    elif pending:
        result = await _get_first_task(pending)  # Wait the next task if previous is None
    else:
        return None  # If no more pending tasks

    try:
        await gather
    except asyncio.CancelledError:
        pass

    return result

frames = {
    "5m": 288,
    "1h": 840,
    "1d": 5000,
}

async def fetch_ohlcv_loop(exchange: BaseExchange, symbol: str, timeframe: str):
    limit = frames[timeframe]
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    if len(ohlcv) < int(limit) and timeframe != "1d":
        raise Exception("Not enough data")

    if timeframe == "5m":
        _check_fresh(ohlcv)

    result = {"prices": [tuple((item[0], item[4])) for item in ohlcv],
              "exchange": exchange.id}
    return result


def _check_fresh(ohlcv: list) -> NoReturn:
    """
        Check if the values received from exchange are actual
    """
    stmp = ohlcv[-1][0]
    now = int(time.time()) * 1000
    diff = now - stmp
    if diff > 900_000:  # more 15 minutes
        raise Exception("Too old values")


async def main():
    from src.deps.markets import AllMarketsLoader
    from src.mapper import get_mapper
    exs = AllMarketsLoader(['mexc', 'binance'])
    ex_markets = await exs.start()
    mapper = await get_mapper(ex_markets)


    lg.info("Request")
    mapped_markets = mapper.get('bitcoin')
    if not mapped_markets:
        raise HTTPException(status_code=404, detail="cg_id not found in any exchange")
    lg.info(f"{mapped_markets}")
    await fecth_markets_chart(exchanges=mapped_markets,
                              currency='usd',
                              timeframe='1d')
    lg.info("Response")
    await exs.close()


if __name__ == '__main__':
    asyncio.run(main())