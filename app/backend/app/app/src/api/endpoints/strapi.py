from src.lib.schema import UpdateEventFrom

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from starlette import status
from src.db import connection
from src.db.cruds.crud_exchange import ExchangeCRUD
from loguru import logger as lg

router = APIRouter()


@router.post("/")
async def strapi_event(event: UpdateEventFrom, session: AsyncSession = Depends(connection.get_db)):
    lg.debug(event)
    return