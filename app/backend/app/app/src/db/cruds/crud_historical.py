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
from src.db.models import Historical, FiveMinExchangeVolumeChart, OneHourExchangeVolumeChart, OneDayExchangeVolumeChart, Exchange, Ticker
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
        stmt = select(Historical.cg_id.label("hdr_id"),
                      Historical.price_usd.label("price"),
                      Historical.volume_usd.label("volume"),
                      Historical.price_btc,
                      Historical.volume_btc,
                      Historical.timestamp.label("stamp"))
        conditions = []
        for coin in coins:
            condition = (Historical.cg_id == coin.hdr_id) & (Historical.timestamp == coin.stamp)
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

    async def save_exchange_chart_volumes(self, session: AsyncSession):
        five_min_stmt = text(
            """
                INSERT INTO exchange_volume_chart_5m(exchange_id, volume_usd, timestamp)
                    SELECT 
                        e.id,
                        COALESCE(sum(t.volume_usd), 0) AS volume,
                        round(extract(epoch FROM date_bin('5 min', now(), '2024-1-1'))) as timestamp 
                    FROM 
                        exchange e
                    LEFT JOIN (
                        SELECT * FROM ticker WHERE last_update > (select round(extract(epoch from now()) - 3600))
                    ) t ON e.id = t.exchange_id
                    GROUP BY e.id
                ON CONFLICT ON CONSTRAINT exchange_stamp_unique_5m
                DO UPDATE SET
                    volume_usd = EXCLUDED.volume_usd
            """
        )
        one_hour_stmt = text(
            """
                INSERT INTO exchange_volume_chart_1h(exchange_id, volume_usd, timestamp)
                    SELECT 
                        e.id,
                        COALESCE(sum(t.volume_usd), 0) AS volume,
                        round(extract(epoch FROM date_bin('1 hour', now(), '2024-1-1'))) as timestamp 
                    FROM 
                        exchange e
                    LEFT JOIN (
                        SELECT * FROM ticker WHERE last_update > (select round(extract(epoch from now()) - 3600))
                    ) t ON e.id = t.exchange_id
                    GROUP BY e.id
                ON CONFLICT ON CONSTRAINT exchange_stamp_unique_1h
                DO UPDATE SET
                    volume_usd = EXCLUDED.volume_usd
            """
        )
        one_day_stmt = text(
            """
                INSERT INTO exchange_volume_chart_1d(exchange_id, volume_usd, timestamp)
                    SELECT 
                        e.id,
                        COALESCE(sum(t.volume_usd), 0) AS volume,
                        round(extract(epoch FROM date_bin('1 day', now(), '2024-1-1'))) as timestamp 
                    FROM 
                        exchange e
                    LEFT JOIN (
                        SELECT * FROM ticker WHERE last_update > (select round(extract(epoch from now()) - 3600))
                    ) t ON e.id = t.exchange_id
                    GROUP BY e.id
                ON CONFLICT ON CONSTRAINT exchange_stamp_unique_1d
                DO UPDATE SET
                    volume_usd = EXCLUDED.volume_usd
            """
        )

        await session.execute(five_min_stmt)
        await session.execute(one_hour_stmt)
        await session.execute(one_day_stmt)
        await session.commit()

    async def delete_old_chart_data(self, session: AsyncSession):
        day_ago = int(time.time()) - 3600 * 25
        month_ago = int(time.time()) - 3600 * 24 * 32
        year_ago = int(time.time()) - 3600 * 24 * 366
        min_stmt = delete(FiveMinExchangeVolumeChart).where(FiveMinExchangeVolumeChart.timestamp < day_ago)
        month_stmt = delete(OneHourExchangeVolumeChart).where(OneHourExchangeVolumeChart.timestamp < month_ago)
        day_stmt = delete(OneDayExchangeVolumeChart).where(OneDayExchangeVolumeChart.timestamp < year_ago)
        await session.execute(min_stmt)
        await session.execute(month_stmt)
        await session.execute(day_stmt)
        await session.commit()


    async def store_gecko_data(self, session: AsyncSession, data: list):
        stmt = insert(OneHourExchangeVolumeChart).values(data)
        do_update = stmt.on_conflict_do_update(
            index_elements=[OneHourExchangeVolumeChart.exchange_id, OneHourExchangeVolumeChart.timestamp],
            set_=dict(
                volume_usd=stmt.excluded.volume_usd,
            ))
        await session.execute(do_update)
        await session.commit()


    async def get_charts(self, session: AsyncSession, exchange_name: str, chart_params: dict):
        type = chart_params["type"]
        if type == "5_minute":
            table = FiveMinExchangeVolumeChart
        elif type == "hourly":
            table = OneHourExchangeVolumeChart
        else:
            table = OneDayExchangeVolumeChart

        stmt = (select(Exchange.ccxt_name, table.volume_usd, table.timestamp)
                .join(Exchange, Exchange.id == table.exchange_id)
                .where(Exchange.ccxt_name == exchange_name)
                .order_by(table.timestamp.desc())
                .limit(chart_params["limit"])
                )
        result = await session.execute(stmt)
        result = result.mappings()
        result = {res['timestamp']: dict(res) for res in result}
        return result


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