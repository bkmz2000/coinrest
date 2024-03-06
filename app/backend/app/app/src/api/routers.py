from fastapi import APIRouter

from src.api.endpoints import exchange
from src.api.endpoints import ticker
from src.api.endpoints import strapi

api_router = APIRouter()
api_router.include_router(exchange.router, prefix="/exchange", tags=["exchange"])
api_router.include_router(ticker.router, prefix="/ticker", tags=["ticker"])
api_router.include_router(strapi.router, prefix="/strapi", tags=["strapi"])
