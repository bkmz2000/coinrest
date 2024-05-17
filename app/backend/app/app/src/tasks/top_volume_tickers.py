import asyncio
import sys
import traceback

from loguru import logger as lg
from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_ticker import TickerCRUD


async def main():
    lg.info("Start top volumes copying")
    try:
        crud = TickerCRUD()
        async with AsyncSessionFactory() as session:
            await crud.save_max_volume_tickers(session=session)
            lg.info("Top volumes copied")
    except Exception as e:
        lg.error(e.with_traceback(traceback.print_exc(100, sys.stdout)))


if __name__ == '__main__':
    asyncio.run(main())
