import asyncio
import time
from collections import defaultdict
from typing import Iterable, Literal
from ccxt.async_support.base.exchange import BaseExchange
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger as lg

from src.db.crud import get_coins_from_db
from src.lib import utils
from src.lib import schema


async def get_coins(session: AsyncSession) -> dict[str, utils.CoinResponse]:
    coins = await get_coins_from_db(session=session)
    result = {}
    for coin in coins:
        result[coin.cg_id] = utils.CoinResponse(usd=coin.price_usd,
                                                usd_24h_vol=coin.volume_usd,
                                                btc=coin.price_btc,
                                                btc_24h_vol=coin.volume_btc,
                                                )
    return result


async def fetch_markets_chart(exchanges: list[utils.Match],
                              timeframe: Literal['5m', '1h', '1d'],
                              stamps: list[int]) -> list[schema.HistoricalResponse] | None:
    result = await fetch_all_ohlcv(exchanges, timeframe, stamps)
    return result


async def fetch_all_ohlcv(exchanges: list[utils.Match],
                          timeframe: Literal['5m', '1h', '1d'],
                          stamps: list[int]) -> list[schema.HistoricalResponse] | None:
    result_list = []
    results = defaultdict(list)
    tasks = [asyncio.create_task(fetch_ohlcv_loop(exchange, timeframe, stamps, results))
             for exchange in exchanges]
    await _get_first_task(tasks, results)
    for stamp, prices in results.items():
        if prices:
            result_list.append(
                schema.HistoricalResponse(
                    cg_id=exchanges[0].cg_id,
                    price=sorted(prices)[len(prices) // 2],
                    stamp=stamp
                )
            )
    return result_list


async def fetch_ohlcv_loop(match: utils.Match,
                           timeframe: Literal['5m', '1h', '1d'],
                           stamps: list[int],
                           results: dict):
    if match.symbol == "USDT":
        ohlcvs = await match.exchange.fetch_ohlcv(match.symbol + "/USD", timeframe, limit=100)
    else:
        ohlcvs = await match.exchange.fetch_ohlcv(match.symbol + "/USDT", timeframe, limit=100)

    for ohlcv in ohlcvs:
        stamp = int(ohlcv[0]) // 1000
        if stamp in stamps:
            if ohlcv[4]:
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
            result = task.result()
            break

    gather = asyncio.gather(*pending, return_exceptions=True)

    res_number = list(results.values())
    if res_number:
        res_number = len(res_number[0])
    else:
        res_number = 0

    if res_number > 2:  # If enough number of results,
        gather.cancel()  # cancel other tasks
    elif pending:
        await _get_first_task(pending, results)  # Wait the next task if previous is None
    else:
        return None  # If no more pending tasks

    try:
        await gather
    except asyncio.CancelledError:
        pass
