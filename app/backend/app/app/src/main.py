from redis.asyncio import Redis
from fastapi import FastAPI, Depends

from contextlib import asynccontextmanager
from loguru import logger as lg
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware


from src.db.connection import get_db, engine
from src.rest import get_coins
from src.worker import last_tickers_task, old_update_mapper_task
from src.api.routers import api_router
from src.lib.utils import CoinResponse
from sqladmin import Admin
from src.admin import views

r: Redis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    last_tickers_task.apply_async()
    yield


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


@app.get("/update")
async def update():
    """
        Update mapper
    """
    old_update_mapper_task.apply_async()
    return {"message": "Mapper updating..."}

