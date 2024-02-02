from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.db.connection import Mapper
from src.lib.utlis import BaseMapper as BaseMapperSchema


async def get_mapper_data(session: AsyncSession):
    stmt = select(Mapper.cg_id, Mapper.exchange, Mapper.symbol)
    result = await session.execute(stmt)
    result = result.mappings()
    result = [BaseMapperSchema.model_validate(res) for res in result]
    return result


async def set_mapper_data(session: AsyncSession, mapper: BaseMapperSchema):
    stmt = insert(Mapper).values(
        cg_id=mapper.cg_id,
        exchange=mapper.exchange,
        symbol=mapper.symbol,
    )
    do_nothing = stmt.on_conflict_do_nothing(index_elements=[Mapper.cg_id, Mapper.exchange])
    await session.execute(do_nothing)
    await session.commit()
