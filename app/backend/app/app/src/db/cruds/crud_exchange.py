import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null
from loguru import logger as lg

from src.db.models import Exchange, ExchangeMapper
from src.lib.schema import ExchangeResponse, Market, ExchangeNameResponse


class ExchangeCRUD:
    async def get_exchange_names(self, session: AsyncSession):
        stmt = select(Exchange.ccxt_name.label("name")).where(Exchange.cg_identifier.is_not(null()))
        result = await session.execute(stmt)
        result = result.mappings()
        return [ExchangeNameResponse.model_validate(res) for res in result]


    async def get_exchanges(self, session: AsyncSession):
        stmt = select(Exchange.id, Exchange.cg_identifier).where(Exchange.cg_identifier.is_not(null()))
        result = await session.execute(stmt)
        result = result.mappings()
        return [ExchangeResponse.model_validate(res) for res in result]

    async def get_cg_ids(self, session: AsyncSession):
        stmt = select(Exchange.cg_identifier).where(Exchange.cg_identifier.is_not(null()))
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def update(self, session: AsyncSession, exchange: Market):
        stmt = (update(Exchange)
        .where(Exchange.cg_identifier == exchange.identifier)
        .values(
            {
                Exchange.logo: exchange.logo,
                Exchange.full_name: exchange.name,
                Exchange.centralized: exchange.centralized,
                Exchange.trust_score: exchange.trust_score
            }
        )
        )
        await session.execute(stmt)
        await session.commit()


    async def save_mappings(self, session: AsyncSession, exchange_id: int, mapped: dict):
        mapping_list = [dict(exchange_id=exchange_id, symbol=symbol, cg_id=gecko) for symbol, gecko in mapped.items()]
        stmt = insert(ExchangeMapper).values(mapping_list)
        update = stmt.on_conflict_do_update(
            index_elements=[ExchangeMapper.exchange_id, ExchangeMapper.symbol],
            set_=dict(
                symbol=stmt.excluded.symbol,
                cg_id=stmt.excluded.cg_id,
                updated_at=datetime.datetime.now()
            )
        )
        await session.execute(update)
        await session.commit()