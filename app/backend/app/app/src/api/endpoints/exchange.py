from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from starlette import status
from src.db import connection
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.db.cruds.crud_ticker import TickerCRUD

router = APIRouter()


@router.get("/")
async def get_exchange(session: AsyncSession = Depends(connection.get_db)):
    """
        Get exchange list
    """
    ex = ExchangeCRUD()
    return await ex.get_exchange_names(session=session)
