import asyncio
import datetime
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null
from sqlalchemy.dialects.postgresql import insert
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.models import ExchangeMapper, QuoteMapper, Ticker, Exchange, OrderBook
from src.lib import utils
from src.lib import schema


async def get_cg_mapper(session: AsyncSession, exchange_id: str) -> dict[str, str]:
    """
        For current exchange get all mapped symbols to coingecko ids
    """
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
    """
        Get all mapping info (symbol, coingecko_id) for a given exchange ids
    """
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
    """
        Update quote currencies
    """
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
                        last_update=int(time.time()),
                        on_create_id="hdlr-"+ticker.base.lower(),
                        created_at=datetime.datetime.now()
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


async def save_orders(session: AsyncSession, orders: list[utils.OrderBook]):
    orders_to_insert = [order.model_dump() for order in orders]
    insert_stmt = insert(OrderBook).values(orders_to_insert)
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[OrderBook.cg_id],
        set_=dict(
            bids=insert_stmt.excluded.bids,
            asks=insert_stmt.excluded.asks,
            exchange=insert_stmt.excluded.exchange,
            updated_at=datetime.datetime.utcnow()
        )
    )
    await session.execute(update_stmt)
    await session.commit()


async def get_order_books(session: AsyncSession, cg_id: str) -> utils.OrderBookFromDB:
    stmt = (select(OrderBook.cg_id, Ticker.price_usd.label("last_price"), OrderBook.base, OrderBook.quote, OrderBook.exchange, OrderBook.bids, OrderBook.asks)
            .where(OrderBook.cg_id == cg_id)
            .where(OrderBook.base == Ticker.base)
            .where(OrderBook.quote == Ticker.quote)
            .where(Ticker.exchange_id == Exchange.id)
            .where(OrderBook.exchange == Exchange.ccxt_name)
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [utils.OrderBookFromDB.model_validate(res) for res in result]
    if result:
        return result[0]


async def get_db_tickers(session: AsyncSession) -> list[utils.TickerToMatch]:
    stmt = (select(Ticker.id, Ticker.exchange_id, Ticker.base, Ticker.price_usd).
            where(Ticker.price_usd > 0).
            where(Ticker.base_cg.is_(null()))
            )
    result = await session.execute(stmt)
    result = result.mappings()
    result = [utils.TickerToMatch.model_validate(res) for res in result]
    return result


async def save_matched_tickers(session: AsyncSession, tickers: list[utils.TickerMatched]):
    ticker_list = [ticker.model_dump() for ticker in tickers]
    await session.execute(update(Ticker), ticker_list)
    await session.commit()


async def main():
    ...

if __name__ == "__main__":
    asyncio.run(main())
