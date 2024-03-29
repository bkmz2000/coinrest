from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from starlette import status
from src.db import connection
from src.db.cruds.crud_ticker import TickerCRUD

router = APIRouter()


@router.get("/gecko/{cg_id}")
async def get_ticker(cg_id: str, session: AsyncSession = Depends(connection.get_db)):
    """
        Get tickers by gecko
    """
    ticker = TickerCRUD()
    result = await ticker.get_ticker_by_cg(session=session, cg_id=cg_id)
    return result

@router.get("/exchange/{exchange}")
async def get_ticker(exchange: str, session: AsyncSession = Depends(connection.get_db)):
    """
        Get tickers by exchange
    """
    ticker = TickerCRUD()
    result = await ticker.get_ticker_by_exchange(session=session, exchange_name=exchange)
    return result

@router.get("/")
async def get_ticker(session: AsyncSession = Depends(connection.get_db)):
    """
        Get top tickers
    """
    ticker = TickerCRUD()
    result = await ticker.get_top_tickers(session=session)
    return result
