import os

import ccxt
import redis.asyncio as redis

from redis.asyncio import Redis
from fastapi import FastAPI, HTTPException, Depends
from ccxt.async_support.base.exchange import BaseExchange

from contextlib import asynccontextmanager
from loguru import logger as lg
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps.markets import AllMarketsLoader
from src.lib.utlis import GeckoMarkets, ChartResponse
from src.mapper import get_mapper, update_mapper
from src.service.logic import fetch_charts
from src.db.connection import get_db, AsyncSessionFactory

r: Redis = None
ex_markets: list[BaseExchange] = []
mapper: dict[str, list[GeckoMarkets]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ex_markets, mapper, r
    exs = AllMarketsLoader(ccxt.exchanges)
    # exs = AllMarketsLoader(['binance', 'mexc', 'hitbtc3'])
    ex_markets = await exs.start()
    r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.environ.get("REDIS_PORT")), decode_responses=True)
    # r = redis.Redis(host="0.0.0.0", port=6389, decode_responses=True)
    async with AsyncSessionFactory() as session:
        mapper = await get_mapper(session=session, exchanges=ex_markets)

    yield

    await exs.close()
    await r.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/ping/{val}")
async def monitor(val: int):
    lg.debug("CALL")
    return {"ping": val}


@app.get("/api/coins/{cg_id}/markets_chart/", response_model=ChartResponse | None)
async def markets_chart(cg_id: str, currency: str, timeframe: str):
    mapped_markets = mapper.get(cg_id)
    if not mapped_markets:
        raise HTTPException(status_code=404, detail=f"{cg_id} does not matched with any market symbol")

    result = await fetch_charts(r, mapped_markets, cg_id, currency, timeframe)

    if not result:
        raise HTTPException(status_code=400, detail="No fast exchanges available")
    return result


@app.get("/update")
async def update(session: AsyncSession = Depends(get_db)):
    """
        Update mapper
    """
    exs = AllMarketsLoader(ccxt.exchanges)
    # exs = AllMarketsLoader(['binance', 'mexc'])
    new_ex_markets = await exs.start()
    await update_mapper(exchanges=new_ex_markets, session=session)
    global mapper
    mapper = await get_mapper(session=session, exchanges=ex_markets)
    await exs.close()
