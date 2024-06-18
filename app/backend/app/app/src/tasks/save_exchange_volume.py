from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_historical import HistoricalCRUD


async def main():
    """
        Update exchanges volumes chart data
    """
    async with AsyncSessionFactory() as session:
        historical_crud = HistoricalCRUD()
        await historical_crud.save_exchange_chart_volumes(session=session)
        await historical_crud.delete_old_chart_data(session=session)
