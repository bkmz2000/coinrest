import os
import redis.asyncio as redis
from redis.asyncio import Redis
from fastapi import FastAPI, HTTPException, Depends
from ccxt.async_support.base.exchange import BaseExchange

from contextlib import asynccontextmanager
from loguru import logger as lg
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

from src.deps.markets import AllMarketsLoader
from src.lib.utils import GeckoMarkets, ChartResponse, CoinResponse
from src.rest import get_coins
from src.tasks.mapper import get_mapper
from src.service.logic import fetch_charts
from src.db.connection import get_db, AsyncSessionFactory, engine
from src.worker import update_last_price, old_update_mapper_task
from src.api.routers import api_router
from sqladmin import Admin
from src.admin import views

r: Redis = None
ex_markets: list[BaseExchange] = []
mapper: dict[str, list[GeckoMarkets]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ex_markets, mapper, r
    # exs = AllMarketsLoader(exchange_names=['binance'])
    exs = AllMarketsLoader()
    await exs.start()
    ex_markets = exs.get_target_markets(target='ohlcv')
    r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.environ.get("REDIS_PORT")), decode_responses=True)
    # r = redis.Redis(host="0.0.0.0", port=6389, decode_responses=True)
    async with AsyncSessionFactory() as session:
        mapper = await get_mapper(session=session, exchanges=ex_markets)
    update_last_price.apply_async()

    yield

    await exs.close()
    await r.aclose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

admin = Admin(app, engine)
admin.add_view(views.ExchangesAdmin)
admin.add_view(views.TickerAdmin)


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


@app.get("/api/coins/markets_price")
async def coins(session: AsyncSession = Depends(get_db)):
    return await get_coins(session=session)


@app.get("/update")
async def update(session: AsyncSession = Depends(get_db)):
    """
        Update mapper
    """
    old_update_mapper_task.apply_async()
    return {"message": "Mapper updating..."}

