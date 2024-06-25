import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_last import LastCRUD
from src.db.cruds.crud_ticker import TickerCRUD
from src.lib.schema import NewTickerResponse


async def get_new_tickers(session: AsyncSession):
    ticker_crud, last_crud = TickerCRUD(), LastCRUD()
    new_tickers = await ticker_crud.new(session=session)
    last_tickers = await last_crud.get_last_with_symbols(session=session)
    new_tickers_response = []

    for new_ticker in new_tickers:
        matched_price = last_tickers.get(new_ticker.base)
        if matched_price is not None and matched_price * 0.7 <= new_ticker.price_usd <= matched_price * 1.3:
            new_tickers_response.append(NewTickerResponse(
                base=new_ticker.base,
                quote=new_ticker.quote,
                price_usd=new_ticker.price_usd,
                on_create_id=new_ticker.on_create_id,
                created_at=new_ticker.created_at,
                exchange=new_ticker.exchange,
                new_for_market=False,
                new_for_exchange=True,

            ))
        else:
            # very new coin
            similar_tickers = await ticker_crud.get_prices_by_symbol(session=session, symbol=new_ticker.base)
            create_times = [similar_ticker.created_at for similar_ticker in similar_tickers if
                            similar_ticker.created_at]
            if create_times:
                min_create_time = min(create_times)
            else:
                min_create_time = 0

            if new_ticker.created_at <= min_create_time:
                new_for_market = True
            else:
                new_for_market = False
            new_tickers_response.append(NewTickerResponse(
                base=new_ticker.base,
                quote=new_ticker.quote,
                price_usd=new_ticker.price_usd,
                on_create_id=new_ticker.on_create_id,
                created_at=new_ticker.created_at,
                exchange=new_ticker.exchange,
                new_for_market=new_for_market,
                new_for_exchange=True,
            ))
    return sorted(new_tickers_response, key=lambda x: x.created_at, reverse=True)


async def main():
    async with AsyncSessionFactory() as session:
        res = await get_new_tickers(session)


if __name__ == "__main__":
    asyncio.run(main())
