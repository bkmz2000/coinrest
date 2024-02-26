from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null
from loguru import logger as lg

from src.db.connection import Exchange
from src.lib.schema import ExchangeResponse


class ExchangeCRUD:
    async def get_exchanges(self, session: AsyncSession):
        stmt = select(Exchange.name, Exchange.trust).order_by(Exchange.name)
        result = await session.execute(stmt)
        result = result.mappings()
        return [ExchangeResponse.model_validate(res) for res in result]
