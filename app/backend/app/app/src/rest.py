import asyncio
import time
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
    result = await fetch_all_ohlcv(exchanges,timeframe, stamps)
    return result


async def fetch_all_ohlcv(exchanges: list[utils.Match],
                          timeframe: Literal['5m', '1h', '1d'],
                          stamps: list[int]) -> list[schema.HistoricalResponse] | None:
    tasks = [asyncio.create_task(fetch_ohlcv_loop(exchange, timeframe, stamps))
             for exchange in exchanges]
    result = await _get_first_task(tasks)
    return result


async def fetch_ohlcv_loop(match: utils.Match,
                           timeframe: Literal['5m', '1h', '1d'],
                           stamps: list[int]) -> list[schema.HistoricalResponse] | None:
    result = []
    if match.symbol == "USDT":
        ohlcvs = await match.exchange.fetch_ohlcv(match.symbol + "/USD", timeframe, limit=100)
    else:
        ohlcvs = await match.exchange.fetch_ohlcv(match.symbol + "/USDT", timeframe, limit=100)

    for ohlcv in ohlcvs:
        stamp = int(ohlcv[0]) // 1000
        if stamp in stamps:
            result.append(schema.HistoricalResponse(
                cg_id=match.cg_id,
                stamp=stamp,
                price=ohlcv[4]
            ))

    return result


async def _get_first_task(tasks: Iterable[asyncio.Task]) -> list[schema.HistoricalResponse] | None:
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
