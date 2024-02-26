from fastapi import APIRouter

from src.api.endpoints import exchange
from src.api.endpoints import ticker


api_router = APIRouter()
api_router.include_router(exchange.router, prefix="/exchange", tags=["exchange"])
api_router.include_router(ticker.router, prefix="/ticker", tags=["ticker"])