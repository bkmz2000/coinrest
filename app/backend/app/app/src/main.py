import asyncio
import os
import time

import redis.asyncio as redis
from redis.asyncio import Redis
from fastapi import FastAPI, Depends

from contextlib import asynccontextmanager
from loguru import logger as lg
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

from src.db.connection import get_db, engine, AsyncSessionFactory
from src.rest import get_coins
from src.worker import last_tickers_task, old_update_mapper_task
from src.api.routers import api_router
from src.lib.utils import CoinResponse
from src.lib.schema import HistoricalRequest, HistoricalResponse
from src.deps.historical import HistoricalMarkets
from sqladmin import Admin
from src.admin import views
from src.rest import fetch_markets_chart

# r: Redis = None
markets: HistoricalMarkets = None

async def get_markets():
    global markets
    markets = HistoricalMarkets()
    async with AsyncSessionFactory() as session:
        await markets.load_markets(session=session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # global r
    # r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.environ.get("REDIS_PORT")), decode_responses=True)
    last_tickers_task.apply_async()

    loop = asyncio.get_running_loop()
    asyncio.run_coroutine_threadsafe(get_markets(), loop)

    yield

    # await r.aclose()
    await markets.close_markets()


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


@app.get("/api/coins/markets_price", response_model=dict[str, CoinResponse])
async def coins(session: AsyncSession = Depends(get_db)):
    return await get_coins(session=session)


@app.post("/api/coins/historical", response_model=list[HistoricalResponse])
async def coins_historical(coins: list[HistoricalRequest]):
    response = []

    beg = 0
    step = 300
    end = len(coins)
    for i in range(beg, end, step):
        tasks = []
        for coin in coins[i:i+step]:
            matched_exchanges = markets.mapper[coin.cg_id]
            # lg.info(matched_exchanges)
            if matched_exchanges:
                tasks.append(asyncio.create_task(fetch_markets_chart(exchanges=matched_exchanges,
                                                                     timeframe=coin.timeframe,
                                                                     stamps=coin.stamps)))
        result = await asyncio.gather(*tasks)
        _ = [response.extend(l) for l in result]

    return response


@app.post("/update")
async def update():
    """
        Update mapper
    """
    old_update_mapper_task.apply_async()
    return {"message": "Mapper updating..."}
