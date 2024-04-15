import asyncio

from loguru import logger as lg

from src.api.rest.historical import fetch_markets_chart
from src.deps.historical import HistoricalMarkets
from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_ticker import TickerCRUD
from src.db.cruds.crud_historical import HistoricalCRUD


async def main(**kwargs):
    """
        Update historical table with data from OHLC
    """
    limit = kwargs.get("limit")
    if limit:
        offset = 0
        limit = limit
    else:
        offset = 500
        limit = 10000
    lg.info(f"Start updating historical data from exchanges OHLCV with limit: {limit}")
    async with AsyncSessionFactory() as session:
        ticker_crud, historical_crud = TickerCRUD(), HistoricalCRUD()
        coins = await ticker_crud.get_tickers(session=session, limit=limit, offset=offset)
        markets = HistoricalMarkets()
        await markets.load_markets(session=session)
        l = len(coins)
        for i, coin in enumerate(coins):
            lg.info(f"{coin} {i + 1}/{l}")
            result = []
            mapped_market = markets.mapper[coin]
            if mapped_market:
                try:
                    result = await fetch_markets_chart(exchanges=mapped_market, timeframe="5m")
                except Exception as e:
                    lg.warning(e)
                if result:
                    await historical_crud.set_data(session=session, values=result)
        await markets.close_markets()
    lg.info(f"historical data from exchanges OHLCV updated successfully")


if __name__ == '__main__':
    asyncio.run(main())

