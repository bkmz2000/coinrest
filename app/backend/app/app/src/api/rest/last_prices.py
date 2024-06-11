import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.cruds.crud_last import LastCRUD
from src.db.cruds.crud_ticker import TickerCRUD
from src.lib import schema
from src.lib.schema import NewCoinResponse


async def get_coins(session: AsyncSession) -> dict[str, schema.PriceResponse]:
    crud = LastCRUD()
    coins = await crud.get_coins_from_db(session=session)
    result = {}
    for coin in coins:
        result[coin.cg_id] = schema.PriceResponse(usd=coin.price_usd,
                                                  usd_24h_vol=coin.volume_usd,
                                                  btc=coin.price_btc,
                                                  btc_24h_vol=coin.volume_btc,
                                                  )
    return result


async def get_new_tickers(session: AsyncSession):
    ticker_crud, last_crud = TickerCRUD(), LastCRUD()
    new_tickers = await ticker_crud.new(session=session)
    last_tickers = await last_crud.get_last_with_symbols(session=session)
    new_coins = []

    for new_ticker in new_tickers:
        for last_ticker in last_tickers:
            if new_ticker.base == last_ticker.base:
                if last_ticker.price_usd * 0.95 <= new_ticker.price_usd <= last_ticker.price_usd * 1.05:
                    # new coin for exchange
                    new_coins.append(NewCoinResponse(
                        cg_id=last_ticker.cg_id,
                        base=new_ticker.base,
                        quote=new_ticker.quote,
                        on_create_id=new_ticker.on_create_id,
                        created_at=new_ticker.created_at,
                        exchange=new_ticker.exchange,
                        new_for_market=False,
                        new_for_exchange=True,

                    ))
                    break
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
            new_coins.append(NewCoinResponse(
                cg_id="",
                base=new_ticker.base,
                quote=new_ticker.quote,
                on_create_id=new_ticker.on_create_id,
                created_at=new_ticker.created_at,
                exchange=new_ticker.exchange,
                new_for_market=new_for_market,
                new_for_exchange=True,
            ))
    return sorted(new_coins, key=lambda x: x.created_at, reverse=True)


async def main():
    from src.db.connection import AsyncSessionFactory
    async with AsyncSessionFactory() as session:
        await get_new_tickers(session)


if __name__ == "__main__":
    asyncio.run(main())
