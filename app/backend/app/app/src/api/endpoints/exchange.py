from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from starlette import status
from src.db import connection
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.db.cruds.crud_ticker import TickerCRUD
from src.lib.schema import TopExchangeResponse, PairsResponse

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