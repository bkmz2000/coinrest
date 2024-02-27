import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from src.db.connection import Ticker, Exchange
from src.lib.schema import TickerResponse


class TickerCRUD:
    async def get_tickers(self, session: AsyncSession):
        stmt = select(Ticker.base_cg).distinct()
        result = await session.execute(stmt)
        result = result.mappings()
        return [dict(res) for res in result]

    async def get_ticker_by_exchange(self, session: AsyncSession, exchange_name: str):
        stmt = (
            select(Exchange.name,
                   Ticker.base,
                   Ticker.quote,
                   Ticker.base_cg,
                   Ticker.price_usd,
                   Ticker.volume_usd,
                   Ticker.last_update)
            .join(Exchange, Exchange.id == Ticker.exchange_id)
            .where(Exchange.name == exchange_name)
            .order_by(Ticker.volume_usd.desc())
        )
        result = await session.execute(stmt)
        result = result.mappings()
        return [TickerResponse.model_validate(res) for res in result]

    async def get_ticker_by_cg(self, session: AsyncSession, cg_id: str):
        stmt = (
            select(Exchange.name,
                   Ticker.base_cg,
                   Ticker.base,
                   Ticker.quote,
                   Ticker.price_usd,
                   Ticker.volume_usd,
                   Ticker.last_update
                   )
            .join(Exchange, Exchange.id == Ticker.exchange_id)
            .filter(or_(Ticker.base_cg == cg_id, Ticker.quote_cg == cg_id))
            .order_by(Ticker.volume_usd.desc())
        )
        result = await session.execute(stmt)
        result = result.mappings()
        return [TickerResponse.model_validate(res) for res in result]

    async def get_top_tickers(self, session: AsyncSession):
        unix_stamp_now = int(time.time()) - 10800  # 3 hours
        base_volume = (select(Ticker.base_cg.label("gecko"), func.sum(Ticker.volume_usd).label("volume_usd"))
                       .where(Ticker.last_update >= unix_stamp_now)
                       .group_by(Ticker.base_cg).select_from(Ticker))

        quote_volume = (select(Ticker.quote_cg.label("gecko"), func.sum(Ticker.volume_usd).label("volume_usd"))
                        .where(Ticker.last_update >= unix_stamp_now)
                        .group_by(Ticker.quote_cg).select_from(Ticker))

        stmt = (
            base_volume.union_all(quote_volume).subquery()
        )
        new_stmt = (
            select
                (
                stmt.c.gecko.label("base_cg"),
                func.sum(stmt.c.volume_usd).label("volume_usd")
            )
            .group_by(stmt.c.gecko)
            .select_from(stmt)
            .order_by(func.sum(stmt.c.volume_usd).desc())
            .limit(250)
        )
        result = await session.execute(new_stmt)
        result = result.mappings()
        return [dict(res) for res in result]
