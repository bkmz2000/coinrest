import asyncio
import datetime
import time
from dataclasses import asdict

import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null
from sqlalchemy.dialects.postgresql import insert
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.models import ExchangeMapper, QuoteMapper, Ticker, Exchange
from src.lib import utils
from src.lib.schema import TickerInfo, TickerMatched, TickerToMatch
from src.lib.utils import Coin


async def get_mapper_data(session: AsyncSession):
    stmt = (select(ExchangeMapper.cg_id, ExchangeMapper.symbol, Exchange.ccxt_name)
            .join(Exchange, Exchange.id == ExchangeMapper.exchange_id)
            .where(Exchange.id == ExchangeMapper.exchange_id))
    result = await session.execute(stmt)
    result = result.mappings()
    result = [utils.BaseMapper.model_validate(res) for res in result]
    return result


async def get_cg_mapper(session: AsyncSession, exchange_id: str) -> dict[str, str]:
    stmt = (select(ExchangeMapper.cg_id, ExchangeMapper.symbol, Exchange.ccxt_name)
            .join(Exchange, Exchange.id == ExchangeMapper.exchange_id)
            .where(Exchange.id == ExchangeMapper.exchange_id)
            .having(Exchange.ccxt_name == exchange_id).group_by(ExchangeMapper.cg_id, ExchangeMapper.symbol, Exchange.ccxt_name)
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = {
        utils.BaseMapper.model_validate(res).symbol:
            utils.BaseMapper.model_validate(res).cg_id for res in result
    }
    return result


async def get_coins_from_db(session: AsyncSession):
    stmt = text("""
        SELECT gecko as cg_id, sum(volume_usd) as volume, max(price) as price FROM (
                SELECT 
                        q.base_cg as gecko,
                        sum(q.volume_usd) as volume_usd,
                        (SELECT max(price_usd) FROM  
                            (SELECT price_usd, volume_usd FROM ticker WHERE base_cg = q.base_cg) as q1 
                            WHERE q1.volume_usd = (
                                SELECT max(volume_usd) 
                                FROM ticker 
                                WHERE base_cg = q.base_cg 
                                AND last_update >= :stamp)
                        ) as price
                FROM ticker q
                WHERE last_update >= :stamp
                GROUP BY q.base_cg
            UNION ALL 
                SELECT 
                    q.quote_cg as gecko,
                    sum(q.volume_usd) as volume_usd,
                    0 as price
                FROM ticker q
                WHERE q.base_cg IS NOT NULL
                AND last_update >= :stamp
                GROUP BY q.quote_cg
            ) total
            GROUP BY gecko
            ORDER BY sum(volume_usd) DESC;
                """)
    unix_stamp_now = int(time.time()) - 10800  # 3 hours
    result = await session.execute(stmt, params=[{"stamp": unix_stamp_now}])
    result = result.mappings()
    result = [utils.BaseLastVolume.model_validate(res) for res in result]

    return result


async def update_quote_mapper(session: AsyncSession, rates: list[utils.QuoteRate]):
    rates_list = [dict(currency=rate.currency, rate=rate.rate, update_at=rate.update_at) for rate in rates]
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

async def save_tickers(session: AsyncSession, tickers: list[TickerInfo]):
    if not tickers:
        return
    exchange_name = tickers[0].exchange_id
    # stmt = select(Exchange.id).where(Exchange.name == exchange_name).select_from(Exchange).scalar_subquery()
    stmt = select(Exchange.id).where(Exchange.ccxt_name == exchange_name)
    exchange_id = await session.execute(stmt)
    exchange_id = exchange_id.scalar()
    if not exchange_id:
        return
    ticker_list = [dict(exchange_id=exchange_id,
                        base=ticker.base,
                        base_cg=ticker.base_cg,
                        quote=ticker.quote,
                        quote_cg=ticker.quote_cg,
                        price=ticker.price,
                        price_usd=ticker.price_usd,
                        base_volume=ticker.base_volume,
                        quote_volume=ticker.quote_volume,
                        volume_usd=ticker.volume_usd,
                        last_update=int(time.time())
                        ) for ticker in tickers]
    insert_stmt = insert(Ticker).values(ticker_list)
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[Ticker.exchange_id, Ticker.base, Ticker.quote],
        set_=dict(
            price=insert_stmt.excluded.price,
            price_usd=insert_stmt.excluded.price_usd,
            base_cg=insert_stmt.excluded.base_cg,
            quote_cg=insert_stmt.excluded.quote_cg,
            base_volume=insert_stmt.excluded.base_volume,
            quote_volume=insert_stmt.excluded.quote_volume,
            volume_usd=insert_stmt.excluded.volume_usd,
            last_update=int(time.time())
        )
    )
    await session.execute(update_stmt)
    await session.commit()


async def get_db_tickers(session: AsyncSession) -> list[TickerToMatch]:
    stmt = (select(Ticker.id, Ticker.exchange_id, Ticker.base, Ticker.price_usd).
            where(Ticker.price_usd > 0).
            where(Ticker.base_cg.is_(null()))
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [TickerToMatch.model_validate(res) for res in result]
    return result


async def save_matched_tickers(session: AsyncSession, tickers: list[TickerMatched]):
    ticker_list = [ticker.model_dump() for ticker in tickers]
    await session.execute(update(Ticker), ticker_list)
    await session.commit()



async def main():
    ...
    # from src.lib.quotes import active_exchanges

    # async with AsyncSessionFactory() as session:
    # tickers = [TickerMatched(id=6313, base_cg="BTC")]
    # await save_matched_tickers(session, tickers)
    # result = await get_coins_from_db(session=session)
    # l = [TickerInfo(exchange_id='hotcoinglobal', base='ARB', base_cg=None, quote='USDT', quote_cg=None, price=1.839, price_usd=1.8392390699999999, base_volume=3977992.3, quote_volume=0, volume_usd=7316478.8583191605),
    #      TickerInfo(exchange_id='hotcoinglobal', base='BTM', base_cg=None, quote='USDT', quote_cg=None, price=0.010077, price_usd=0.01007831001, base_volume=27628613.855, quote_volume=0, volume_usd=278449.7355772712)
    #      ]
    # await save_tickers(session=session, tickers=l)
    # result = await get_converter(session=session)
    # lg.debug(result)


if __name__ == "__main__":
    asyncio.run(main())
