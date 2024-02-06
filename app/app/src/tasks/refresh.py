import random

from src.deps.markets import AllMarketsLoader
from src.lib.client import fetch_data_from_hodler
from src.service.logic import fetch_markets_chart
from src.db.crud import get_mapper_data
from src.db.connection import AsyncSessionFactory
from loguru import logger as lg
from src.tasks.task import set_cache_task
from src.mapper import get_mapper


async def cache_refresh(timeframe: str) -> None:
    # top_coins = await fetch_data_from_hodler()[:250]
    coins = await fetch_data_from_hodler()
    top_coins = coins[:250]
    exs = AllMarketsLoader(['binance', 'mexc', 'hitbtc3'])

    ex_markets = await exs.start()

    async with AsyncSessionFactory() as session:
        mapper = await get_mapper(session=session, exchanges=ex_markets)
        for coin in top_coins:
            mapped_markets = mapper.get(coin['cgid'])
            if not mapped_markets:
                continue
            if len(mapped_markets) > 10:
                mapped_markets = random.sample(mapped_markets, k=10)

            lg.info(f"{coin['cgid']}: mapped with {len(mapped_markets)} exchanges")
            result = await fetch_markets_chart(exchanges=mapped_markets,
                                               currency="usd",
                                               timeframe=timeframe)
            if result:
                set_cache_task.apply_async(kwargs={
                    "cg_id": coin['cgid'],
                    "currency": "usd",
                    "timeframe": timeframe,
                    "value": result,
                })
    await exs.close()
            # await fetch_charts(r, mapped_markets, coin["cgid"], "usd", timeframe)