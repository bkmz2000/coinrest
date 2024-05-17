from fastapi import APIRouter

from src.api.endpoints import exchange
from src.api.endpoints import ticker
from src.api.endpoints import coin
from src.api.endpoints import depth


api_router = APIRouter()
api_router.include_router(exchange.router, prefix="/exchange", tags=["exchange"])
api_router.include_router(ticker.router, prefix="/ticker", tags=["ticker"])
api_router.include_router(coin.router, prefix="/coins", tags=["coins"])
api_router.include_router(depth.router, prefix="/depth", tags=["depth"])
