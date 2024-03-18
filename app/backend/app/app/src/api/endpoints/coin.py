from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.db import connection

router = APIRouter()


@router.get("/exchanges")
async def get_ticker_exchanges(cg_id: str,
                               limit: int = Query(100),
                               offset: int = Query(0),
                               currency: str = Query('All'),
                               exchange_type: str = Query('All'),
                               trade_type: str = Query('Spot'),
                               id_sort: str = Query('ASC'),
                               exchange_sort: str = Query('ASC'),
                               pair_sort: str = Query('ASC'),
                               volume_sort: str = Query('ASC'),
                               session: AsyncSession = Depends(connection.get_db)):
    """
        Get coin exchanges
    """

    return
