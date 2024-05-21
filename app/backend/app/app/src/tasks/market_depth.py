import asyncio
import sys
import traceback

from src.db.connection import AsyncSessionFactory
from loguru import logger as lg

from src.db.cruds.crud_ticker import TickerCRUD
from src.deps.depth import OrderBookMarket


async def main():
    lg.info("Starting market depth task")
    exchanges = await get_exchanges()
    # exchanges = ['binance']
    await asyncio.gather(*[get_order_books(ex=ex) for ex in exchanges])
    lg.info("Market depth task completed")


async def get_order_books(ex: str):
    """
        Get Order books for coins and store them to db
    """
    try:
        async with OrderBookMarket(exchange_name=ex) as market:
            coins = await market.get_exchange_coins_for_orderbook()
            for i in range(0, len(coins), 20):
                orders = await market.get_order_books(coins[i:i + 20])
                await market.save_order_books(orders)

    except Exception as e:
        err_msg = str(e)
        if "_abort" in err_msg:
            lg.warning(e)  # Library specific error when fails releasing resources
        else:
            lg.error(e.with_traceback(traceback.print_exc(100, sys.stdout)))


async def get_exchanges() -> list[str]:
    """
        Get all exchanges for fetching order books
    """
    crud = TickerCRUD()
    async with AsyncSessionFactory() as session:
        exchanges = await crud.get_depth_exchanges(session=session)
    return exchanges


if __name__ == "__main__":
    asyncio.run(main())
