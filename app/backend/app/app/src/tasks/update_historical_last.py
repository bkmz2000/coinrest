import asyncio
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_historical import HistoricalCRUD


async def main():
    """
        Update historical from last values table
    """
    async with AsyncSessionFactory() as session:
        historical_crud = HistoricalCRUD()
        await historical_crud.copy_from_last_to_history(session=session)
        lg.info("Successfully copied data to history table")
        await historical_crud.delete_old_data(session=session)
        lg.info("Old data removed from history table")

if __name__ == '__main__':
    asyncio.run(main())

