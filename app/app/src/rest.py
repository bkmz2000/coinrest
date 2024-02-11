import asyncio
import time

import ccxt.async_support as ccxt
from ccxt.async_support.base.exchange import BaseExchange
from src.lib.utlis import GeckoMarkets
from loguru import logger as lg
from starlette.exceptions import HTTPException
from collections.abc import Iterable

frames = {
    "5m": 288,
    "1h": 840,
    "1d": 1000,
}


async def fetch_markets_chart(exchanges: list[GeckoMarkets],
                              currency: str,
                              timeframe: str) -> dict[str, list[tuple[int, int]]] | None:
    result = await fetch_all_ohlcv(exchanges, timeframe)
    return result


async def fetch_all_ohlcv(exchanges: list[GeckoMarkets], timeframe: str) -> dict[str, list[tuple[int, int]]] | None:
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


async def main():
    from src.deps.markets import AllMarketsLoader
    from src.mapper import get_mapper
    from src.db.connection import AsyncSessionFactory
    from datetime import datetime

    # exs = AllMarketsLoader(['binance'])
    # exs = AllMarketsLoader(['mexc'])
    # exs = AllMarketsLoader(target='volume', exchange_names=['mexc'])
    exs = AllMarketsLoader(target='volume')
    ex_markets = await exs.start()
    async with AsyncSessionFactory() as session:
        mapper = await get_mapper(ex_markets, session)

    lg.info("Request")
    total = 0
    mapped_markets = mapper.get('polkadot')
    if not mapped_markets:
        raise HTTPException(status_code=404, detail="cg_id not found in any exchange")
    for ex in ex_markets:
        try:
            # chart = await ex.fetch_ohlcv("BTC/USDT", timeframe="1d", limit=100)
            tickers = await ex.fetch_tickers()
            for k, v in tickers.items():
                if k.startswith("DOT/"):
                    volume = v.get("baseVolume")
                    if volume:
                        volume *= 7.19
                        total += volume
                        lg.debug(f'{ex.id}-{k}: {volume}')
            # lg.debug(tickers)
            # volume = ticker.get("quoteVolume")
            # if volume:
            #     total += volume
            # lg.debug(f'{ex.id}, {ticker.get("quoteVolume")}')
        except Exception as e:
            lg.error(e)
    # lg.info(f"{mapped_markets}")
    # chart = await fetch_markets_chart(exchanges=mapped_markets,
    #                                   currency='usd',
    #                                   timeframe='1d')
    # lg.info(chart)
    # lg.info(len(chart.get("prices")))

    # last = datetime.utcfromtimestamp(chart["prices"][-1][0] // 1000).strftime('%Y-%m-%d %H:%M:%S')

    lg.info(total)
    lg.info("Response")
    await exs.close()


def _trunc_time(timestamp: int):
    """
        Strict all timestamps to 00.00.00 (hh.mm.ss)
    """
    trunc = timestamp % 86_400_000
    return timestamp - trunc


if __name__ == '__main__':
    asyncio.run(main())
