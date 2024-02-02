import os
import ccxt
import random

from fastapi import FastAPI, HTTPException, Depends
from ccxt.async_support.base.exchange import BaseExchange
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

from contextlib import asynccontextmanager
from loguru import logger as lg
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps.markets import AllMarketsLoader
from src.lib.utlis import GeckoMarkets
from src.rest import fecth_markets_chart
from src.mapper import get_mapper, update_mapper
from src.db.connection import get_db, AsyncSessionFactory
from src.db.crud import get_mapper_data, set_mapper_data


ex_markets: list[BaseExchange] = []
mapper: dict[str, list[GeckoMarkets]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    global ex_markets, mapper
    exs = AllMarketsLoader(ccxt.exchanges)
    # exs = AllMarketsLoader(['binance', 'mexc'])
    ex_markets = await exs.start()
    async with AsyncSessionFactory() as session:
        mapper = await get_mapper(session=session, exchanges=ex_markets)

    yield

    await exs.close()


app = FastAPI(lifespan=lifespan)


@app.get("/ping/{val}")
@cache(expire=10)
async def monitor(val: int):
    lg.debug("CALL")
    return {"ping": val}


@app.get("/api/coins/{cg_id}/markets_chart/")
@cache(expire=120)
async def markets_chart(cg_id: str, currency: str, timeframe: str):
    mapped_markets = mapper.get(cg_id)
    if not mapped_markets:
        raise HTTPException(status_code=404, detail=f"{cg_id} does not matched with any market symbol")
    if len(mapped_markets) > 10:
        mapped_markets = random.sample(mapped_markets, k=10)

    lg.info(f"{cg_id}: mapped with {len(mapped_markets)} exchanges")
    result = await fecth_markets_chart(exchanges=mapped_markets,
                                       currency=currency,
                                       timeframe=timeframe)
    if not result:
        raise HTTPException(status_code=400, detail="No fast exchanges available")
    return result


@app.get("/update")
async def update(session: AsyncSession = Depends(get_db)):
    exs = AllMarketsLoader(ccxt.exchanges)
    # exs = AllMarketsLoader(['binance', 'mexc'])
    new_ex_markets = await exs.start()
    await update_mapper(exchanges=new_ex_markets, session=session)
    global mapper
    mapper = await get_mapper(session=session, exchanges=ex_markets)
    await exs.close()