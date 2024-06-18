from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from starlette import status
from src.db import connection
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.db.cruds.crud_ticker import TickerCRUD
from src.lib.schema import TopExchangeResponse, PairsResponse, TopPairsResponse, TopCoinsResponse, ExchangeChartResponse
from src.api.rest import charts

router = APIRouter()


@router.get("/")
async def get_exchange(session: AsyncSession = Depends(connection.get_db)):
    """
        Get exchange list
    """
    ex = ExchangeCRUD()
    return await ex.get_exchange_names(session=session)


@router.get("/top", response_model=list[TopExchangeResponse])
async def get_top_exchanges(session: AsyncSession = Depends(connection.get_db), limit: int = Query(3)):
    ex = ExchangeCRUD()
    return await ex.get_top_exchanges(session=session, limit=limit)

@router.get("/pairs", response_model=PairsResponse)
async def get_pairs(session: AsyncSession = Depends(connection.get_db), exchange_name: str = Query()):
    ex = ExchangeCRUD()
    return await ex.get_pairs(session, exchange_name)

@router.get("/top_pairs", response_model=TopPairsResponse)
async def get_top_pairs(session: AsyncSession = Depends(connection.get_db), exchange_name: str = Query()):
    ex = ExchangeCRUD()
    return await ex.get_top_pairs(session, exchange_name)

@router.get("/top_coins", response_model=TopCoinsResponse)
async def get_top_coins(session: AsyncSession = Depends(connection.get_db), exchange_name: str = Query()):
    ex = ExchangeCRUD()
    return await ex.get_top_coins(session, exchange_name)


@router.get("/chart", response_model=ExchangeChartResponse)
async def get_charts(exchange_name: str,
                     period: Literal['24h', '7d', '14d', '1M', '3M', '1Y'],
                     currency: Literal['AUD', 'BRL', 'BTC', 'CAD', 'CHF', 'CNY', 'CZK', 'EUR', 'GBP', 'IDR', 'INR', 'JPY', 'KRW', 'KZT', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RUB', 'SEK', 'SGD', 'TRY', 'USD', 'ZAR'] = Query('USD'),
                     session: AsyncSession = Depends(connection.get_db)):
    return await charts.get_charts(exchange_name, period, currency, session)


