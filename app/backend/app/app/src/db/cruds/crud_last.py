import asyncio
import time
import datetime

import sqlalchemy
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from src.lib import utils, schema
from src.db.models import LastValues, Ticker, Exchange


class LastCRUD:
    """
        CRUD operations for last prices
    """

    async def get_coins_from_db(self, session: AsyncSession) -> list[utils.Last]:
        """
            Get all last prices for every coin.
        """
        delta = datetime.datetime.now() - datetime.timedelta(hours=1)
        stmt = (select(LastValues.cg_id,
                       LastValues.price_usd,
                       LastValues.volume_usd,
                       LastValues.price_btc,
                       LastValues.volume_btc)
                .where(LastValues.last_update > delta)
                .order_by(LastValues.volume_usd.desc())
                )
        result = await session.execute(stmt)
        result = result.mappings()
        result = [utils.Last.model_validate(res) for res in result]
        return result

    async def save_last(self, session: AsyncSession, coins: list[schema.CoinOutput]):
        values = [coin.model_dump() for coin in coins]
        stmt = insert(LastValues).values(values)
        update_stmt = stmt.on_conflict_do_update(
            index_elements=[LastValues.cg_id],
            set_=dict(
                price_usd=stmt.excluded.price_usd,
                volume_usd=stmt.excluded.volume_usd,
                price_btc=stmt.excluded.price_btc,
                volume_btc=stmt.excluded.volume_btc,
                last_update=datetime.datetime.now()
            )
        )
        await session.execute(update_stmt)
        await session.commit()

    async def get_lost_coins(self, session: AsyncSession):
        """
            Get coin that no more trading
        """
        delta = datetime.datetime.now() - datetime.timedelta(days=1)
        stmt = (select(LastValues.cg_id,
                       LastValues.price_usd,
                       LastValues.volume_usd,
                       LastValues.last_update,
                       )
                .where(LastValues.last_update < delta)
                .order_by(LastValues.last_update.desc())
                )
        result = await session.execute(stmt)
        result = result.mappings()
        result = [utils.LastLost.model_validate(res) for res in result]
        return result

    async def get_ids_with_prices(self, session: AsyncSession, limit: int, offset: int) -> list[utils.CoinWithPrice]:
        subq = select(Ticker.base_cg).select_from(Ticker).scalar_subquery()
        stmt = (select(LastValues.cg_id, LastValues.price_usd)
                .where(LastValues.cg_id.in_(subq))
                .order_by(LastValues.volume_usd.desc())
                .limit(limit)
                .offset(offset)
                )
        result = await session.execute(stmt)
        result = result.mappings()
        result = [utils.CoinWithPrice.model_validate(res) for res in result]
        return result

async def main():
    from src.db.connection import AsyncSessionFactory
    async with AsyncSessionFactory() as session:
        crud = LastCRUD()
        # lost = await crud.get_lost_coins(session=session)
        lost = await crud.get_ids_with_prices(session=session, limit=10000, offset=0)
        print(lost)
        print(len(lost))


if __name__ == "__main__":
    asyncio.run(main())