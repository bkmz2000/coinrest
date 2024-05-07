import asyncio
import sys
import traceback
from collections import defaultdict
from typing import Iterable, Literal
from loguru import logger as lg

from src.lib import utils
from src.lib import schema


async def fetch_markets_chart(exchanges: list[utils.Match],
                              timeframe: Literal['5m', '1h', '1d'],
                              price: float) -> list[utils.HistoricalDT] | None:

    result = await fetch_all_ohlcv(exchanges, timeframe, price)
    return result


async def fetch_all_ohlcv(exchanges: list[utils.Match],
                          timeframe: Literal['5m', '1h', '1d'],
                          price: float) -> list[utils.HistoricalDT] | None:
    result_list = []
    results = defaultdict(list)
    tasks = [asyncio.create_task(fetch_ohlcv_loop(exchange, timeframe, results, price))
             for exchange in exchanges]
    try:
        await _get_first_task(tasks, results)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        lg.warning(e.with_traceback(traceback.print_exc(100, sys.stdout)))
    for stamp, prices in results.items():
        result_list.append(
            utils.HistoricalDT(
                cg_id=exchanges[0].cg_id,
                price_usd=sorted(prices)[len(prices) // 2],
                timestamp=stamp
            )
        )
    return result_list


async def fetch_ohlcv_loop(match: utils.Match,
                           timeframe: Literal['5m', '1h', '1d'],
                           results: dict, price: float):
    if match.symbol == "USDT":
        ohlcvs = await match.exchange.fetch_ohlcv(match.symbol + "/USD", timeframe, limit=100)
    else:
        ohlcvs = await match.exchange.fetch_ohlcv(match.symbol + "/USDT", timeframe, limit=100)
    if ohlcvs:
        for ohlcv in ohlcvs:
            stamp = int(ohlcv[0]) // 1000
            if ohlcv[4] and _price_is_not_outlier(price, ohlcv[4]):
                results[stamp].append(ohlcv[4])
    return results


async def _get_first_task(tasks: Iterable[asyncio.Task], results: dict):
    if not tasks:
        return None

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
            task.result()
            break

    gather = asyncio.gather(*pending, return_exceptions=True)

    res_number = list(results.values())
    if res_number:
        res_number = len(res_number[0])
    else:
        res_number = 0

    if res_number > 1:  # If first result is not exception,
        gather.cancel()  # cancel other tasks
    elif pending:
        await _get_first_task(pending, results)
    else:
        return None  # If no more pending tasks

    try:
        await gather
    except asyncio.CancelledError:
        pass

def _price_is_not_outlier(market_price, price):
    if 0.99 <= market_price <= 1.01:  # more strict for stable coins
        return market_price * 0.996 <= price <= market_price * 1.004
    return market_price * 0.96 <= price <= market_price * 1.04
