import logging

from fastapi import FastAPI, Depends
from fastapi.logger import logger as fastapi_logger

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

from src.db.connection import get_db, engine
from src.worker import old_update_mapper_task
from src.api.routers import api_router
from src.lib.schema import HistoricalRequest, HistoricalResponse, PriceResponse
from sqladmin import Admin
from src.admin import views
from src.api.rest.last_prices import get_coins
from src.db.cruds.crud_historical import HistoricalCRUD


gunicorn_error_logger = logging.getLogger("gunicorn.error")
gunicorn_logger = logging.getLogger("gunicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers = gunicorn_error_logger.handlers

fastapi_logger.handlers = gunicorn_error_logger.handlers
fastapi_logger.setLevel(gunicorn_logger.level)


app = FastAPI()

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


@app.get("/api/coins/markets_price", response_model=dict[str, PriceResponse])
async def coins(session: AsyncSession = Depends(get_db)):
    return await get_coins(session=session)


@app.post("/api/coins/historical", response_model=list[HistoricalResponse])
async def coins_historical(coins: list[HistoricalRequest], session: AsyncSession = Depends(get_db)):
    crud = HistoricalCRUD()
    return await crud.get_data(session=session, coins=coins)


@app.post("/update")
async def update():
    """
        Update mapper
    """
    old_update_mapper_task.apply_async()
    return {"message": "Mapper updating..."}
