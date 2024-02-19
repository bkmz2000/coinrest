import asyncio
import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert
from loguru import logger as lg

from src.db.connection import Mapper, Volume, QuoteMapper
from src.lib import utils
from src.lib.utils import Coin


async def get_mapper_data(session: AsyncSession):
    stmt = select(Mapper.cg_id, Mapper.exchange, Mapper.symbol)
    result = await session.execute(stmt)
    result = result.mappings()
    result = [utils.BaseMapper.model_validate(res) for res in result]
    return result


async def set_mapper_data(session: AsyncSession, mapper: utils.BaseMapper):
    stmt = insert(Mapper).values(
        cg_id=mapper.cg_id,
        exchange=mapper.exchange,
        symbol=mapper.symbol,
    )
    do_nothing = stmt.on_conflict_do_nothing(index_elements=[Mapper.cg_id, Mapper.exchange])
    await session.execute(do_nothing)
    await session.commit()


async def get_exchange_cg_ids(session: AsyncSession, exchange_id: str) -> list[dict]:
    stmt = select(Mapper.cg_id, Mapper.symbol).where(Mapper.exchange == exchange_id)
    result = await session.execute(stmt)
    result = result.mappings()
    result = [dict(res) for res in result]
    return result


async def get_cg_mapper(session: AsyncSession, exchange_id: str) -> dict[str, str]:
    stmt = select(Mapper.cg_id, Mapper.symbol, Mapper.exchange).where(Mapper.exchange == exchange_id)
    result = await session.execute(stmt)
    result = result.mappings()
    result = {
        utils.BaseMapper.model_validate(res).symbol:
            utils.BaseMapper.model_validate(res).cg_id for res in result
    }
    # result = [dict(res) for res in result]
    return result


async def save_last_volumes(session: AsyncSession, coins: dict[str, Coin]):
    volumes_list = [dict(cg_id=cg_id, exchange=coin.exchange, volume=coin.volume, price=coin.price) for cg_id, coin in
                    coins.items() if cg_id]
    stmt = insert(Volume).values(volumes_list)
    update = stmt.on_conflict_do_update(
        index_elements=[Volume.cg_id, Volume.exchange],
        set_=dict(
            volume=stmt.excluded.volume,
            price=stmt.excluded.price,
            update=datetime.datetime.now()
        )
    )
    await session.execute(update)
    await session.commit()


async def get_coins_from_db(session: AsyncSession):
    stmt = text("""SELECT 
                        q.cg_id,
                        sum(q.volume) as volume,
                        (SELECT max(price) FROM  
                            (SELECT price, volume FROM last_volumes WHERE cg_id = q.cg_id) as q1 
                            WHERE q1.volume = (SELECT max(volume) FROM last_volumes WHERE cg_id = q.cg_id)
                        ) as price
                FROM last_volumes as q
                GROUP BY q.cg_id
                ORDER BY volume DESC;
                """
                )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [utils.BaseLastVolume.model_validate(res) for res in result]
    return result


async def update_quote_mapper(session: AsyncSession, rates: list[utils.QuoteRate]):
    rates_list = [dict(currency=rate.currency, rate=rate.rate, update_at=rate.update_at) for rate in rates]
    lg.info(rates_list)
    stmt = insert(QuoteMapper).values(rates_list)
    update = stmt.on_conflict_do_update(
        index_elements=[QuoteMapper.currency],
        set_=dict(
            rate=stmt.excluded.rate,
            update_at=stmt.excluded.update_at,
        )
    )
    await session.execute(update)
    await session.commit()


async def get_converter(session: AsyncSession) -> dict[str, float]:
    stmt = select(QuoteMapper.currency, QuoteMapper.rate)
    result = await session.execute(stmt)
    result = result.mappings()
    result = {
        utils.QuoteRate.model_validate(res).currency:
            utils.QuoteRate.model_validate(res).rate for res in result
    }
    return result


async def main():
    async with AsyncSessionFactory() as session:
        # result = await get_coins_from_db(session=session)
        result = await get_converter(session=session)
        lg.debug(result)


if __name__ == "__main__":
    from src.db.connection import AsyncSessionFactory
    asyncio.run(main())
