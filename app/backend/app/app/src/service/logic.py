import random
from redis.asyncio import Redis

from src.lib.utils import GeckoMarkets
from src.rest import fetch_markets_chart
from src.db.cache import get_from_cache
from src.tasks.task import set_cache_task

from loguru import logger as lg


async def fetch_charts(
        r: Redis,
        mapped_markets: list[GeckoMarkets],
        cg_id: str,
        currency: str,
        timeframe: str) -> dict[str, list[tuple[int, int]]] | None:

    cache_result = await get_from_cache(r=r, cg_id=cg_id, currency=currency, timeframe=timeframe)
    if cache_result:
        lg.debug(f"Return result from cache for {cg_id}, {timeframe}")
        return cache_result

    if len(mapped_markets) > 10:
        mapped_markets = random.sample(mapped_markets, k=10)

    lg.info(f"{cg_id}: mapped with {len(mapped_markets)} exchanges")
    result = await fetch_markets_chart(exchanges=mapped_markets,
                                       currency=currency,
                                       timeframe=timeframe)
    if result:
        set_cache_task.apply_async(kwargs={
                "cg_id": cg_id,
                "currency": currency,
                "timeframe": timeframe,
                "value": result,
        })
    return result
