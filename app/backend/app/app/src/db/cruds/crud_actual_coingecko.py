import asyncio
import time
import datetime
from dataclasses import asdict

import sqlalchemy
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete

from src.lib import utils
from src.db.models import ActualCoingecko


class ActualCoingeckoCRUD:
    """
        CRUD operations for actual coingecko
    """
    async def get_actual_geckos(self, session: AsyncSession) -> list[str]:
        stmt = select(ActualCoingecko.cg_id)
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def store_actual_geckos(self, session: AsyncSession, coins: list[utils.ActualCoinIn]):
        values = [asdict(coin) for coin in coins]
        delete_stmt = delete(ActualCoingecko)
        insert_stmt = insert(ActualCoingecko).values(values)
        await session.execute(delete_stmt)
        await session.execute(insert_stmt)
        await session.commit()

async def main():
    from src.db.connection import AsyncSessionFactory
    async with AsyncSessionFactory() as session:
        crud = ActualCoingeckoCRUD()
        geckos = await crud.get_actual_geckos(session=session)
        print(geckos)


if __name__ == "__main__":
    asyncio.run(main())