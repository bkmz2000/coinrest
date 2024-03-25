import asyncio
import datetime
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null
from sqlalchemy.dialects.postgresql import insert
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.models import ExchangeMapper, QuoteMapper, Ticker, Exchange, LastValues
from src.lib import utils
from src.lib import schema


async def get_cg_mapper(session: AsyncSession, exchange_id: str) -> dict[str, str]:
    stmt = (select(ExchangeMapper.cg_id, ExchangeMapper.symbol, Exchange.ccxt_name)
            .join(Exchange, Exchange.id == ExchangeMapper.exchange_id)
            .where(Exchange.id == ExchangeMapper.exchange_id)
            .having(Exchange.ccxt_name == exchange_id).group_by(ExchangeMapper.cg_id, ExchangeMapper.symbol,
                                                                Exchange.ccxt_name)
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = {
        utils.BaseMapper.model_validate(res).symbol:
            utils.BaseMapper.model_validate(res).cg_id for res in result
    }
    return result


async def get_exchange_mapper(session: AsyncSession, exchange_ids: list[str]) -> list[utils.BaseMapper]:
    stmt = (select(ExchangeMapper.cg_id, ExchangeMapper.symbol, Exchange.ccxt_name)
            .join(Exchange, Exchange.id == ExchangeMapper.exchange_id)
            .where(Exchange.id == ExchangeMapper.exchange_id)
            .having(Exchange.ccxt_name.in_(exchange_ids)).group_by(ExchangeMapper.cg_id, ExchangeMapper.symbol,
                                                                   Exchange.ccxt_name)
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [utils.BaseMapper.model_validate(res) for res in result]
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


async def save_tickers(session: AsyncSession, tickers: list[schema.TickerInfo]):
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


async def get_db_tickers(session: AsyncSession) -> list[schema.TickerToMatch]:
    stmt = (select(Ticker.id, Ticker.exchange_id, Ticker.base, Ticker.price_usd).
            where(Ticker.price_usd > 0).
            where(Ticker.base_cg.is_(null()))
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [schema.TickerToMatch.model_validate(res) for res in result]
    return result


async def save_matched_tickers(session: AsyncSession, tickers: list[schema.TickerMatched]):
    ticker_list = [ticker.model_dump() for ticker in tickers]
    await session.execute(update(Ticker), ticker_list)
    await session.commit()


async def get_all_tickers(session: AsyncSession) -> list[schema.TickerSimple]:
    unix_stamp_now = int(time.time()) - 10800  # 3 hours
    stmt = (
        select(Ticker.base_cg, Ticker.price_usd, Ticker.volume_usd)
        .where(Ticker.base_cg.is_not(null()))
        .where(Ticker.price_usd > 0)
        .where(Ticker.volume_usd > 0)
        .where(Ticker.last_update > unix_stamp_now)
        .order_by(Ticker.volume_usd.desc())
    )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [schema.TickerSimple.model_validate(res) for res in result]
    return result


async def save_last(session: AsyncSession, coins: list[schema.CoinOutput]):
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


async def get_coins_from_db(session: AsyncSession):
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


async def main():
    ...

if __name__ == "__main__":
    asyncio.run(main())
