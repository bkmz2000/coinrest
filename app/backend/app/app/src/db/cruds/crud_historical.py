import asyncio
import datetime
import time
from dataclasses import asdict

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null, bindparam, delete, and_, or_
from loguru import logger as lg

from src.lib import schema
from src.db.connection import AsyncSessionFactory
from src.db.models import Historical
from src.lib.schema import HistoricalResponse, NewHistoricalRequest
from src.lib.utils import HistoricalDT


class HistoricalCRUD:
    async def set_data(self, session: AsyncSession, values: list[HistoricalDT]):
        insert_stmt = insert(Historical).values([asdict(val) for val in values])
        do_nothing = insert_stmt.on_conflict_do_nothing(
            index_elements=[Historical.cg_id, Historical.timestamp]
        )
        await session.execute(do_nothing)
        await session.commit()

    async def get_data(self, session: AsyncSession, coins: list[NewHistoricalRequest]) -> list[HistoricalResponse]:
        stmt = select(Historical.cg_id,
                      Historical.price_usd.label("price"),
                      Historical.volume_usd.label("volume"),
                      Historical.price_btc,
                      Historical.volume_btc,
                      Historical.timestamp.label("stamp"))
        conditions = []
        for coin in coins:
            condition = (Historical.cg_id == coin.cg_id) & (Historical.timestamp == coin.stamp)
            conditions.append(condition)
        stmt = stmt.where(or_(*conditions)).limit(120000)
        result = await session.execute(stmt)
        result = result.mappings()
        result = [HistoricalResponse.model_validate(res) for res in result]
        return result


    async def copy_from_last_to_history(self, session: AsyncSession):
        """
            Copy last actual data to historical table
        """
        stmt = text(
            """
                WITH subQuery AS (
                    SELECT 
                        cg_id, price_usd, price_btc, volume_usd, volume_btc, 
                        round(extract(epoch FROM date_bin('5 min', last_update, '2024-1-1'))) as timestamp 
                    FROM last
                )
                INSERT INTO historical(cg_id, price_usd, price_btc, volume_usd, volume_btc, timestamp)
                SELECT 
                    cg_id, price_usd, price_btc, volume_usd, volume_btc, timestamp 
                FROM subQuery
                ON CONFLICT ON CONSTRAINT gecko_stamp_unique
                DO UPDATE SET 
                    price_usd = EXCLUDED.price_usd,
                    volume_usd = EXCLUDED.volume_usd,
                    price_btc = EXCLUDED.price_btc,
                    volume_btc = EXCLUDED.volume_btc;
            """
        )
        await session.execute(stmt)
        await session.commit()

    async def delete_old_data(self, session: AsyncSession):
        stamp_24_hr = int(time.time()) - 86400
        stmt = delete(Historical).where(Historical.timestamp < stamp_24_hr)
        await session.execute(stmt)
        await session.commit()


async def main():
    async with AsyncSessionFactory() as session:
        crud = HistoricalCRUD()
        await crud.copy_from_last_to_history(session=session)
        # data = [HistoricalRequest(cg_id='bitcoin', timeframe='5m', stamps=[1712927700, 1712924400, 1712927100]),
        #         HistoricalRequest(cg_id='solana', timeframe='5m', stamps=[1712927700])]
        # await crud.get_data(session=session, coins=data)
        # await crud.delete_old_data(session=session)

if __name__ == "__main__":
    asyncio.run(main())