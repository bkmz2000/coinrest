import asyncio

import aiohttp
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.db.cruds.crud_historical import HistoricalCRUD
from src.db.cruds.crud_last import LastCRUD


async def main():
    """
        Update exchanges volumes chart data
    """
    async with AsyncSessionFactory() as session:
        historical_crud = HistoricalCRUD()
        await historical_crud.save_exchange_chart_volumes(session=session)
        await historical_crud.delete_old_chart_data(session=session)


async def temp_main():
    async with AsyncSessionFactory() as session:
        crud = ExchangeCRUD()
        historical_crud = HistoricalCRUD()
        last_crud = LastCRUD()
        exchanges = await crud.get_ex_ids(session=session)
        last_btc = await last_crud.get_btc_last(session=session)
        print(last_btc)
        for exchange in exchanges:
            await asyncio.sleep(15)
            if exchange:
                try:
                    print(exchange)
                    volumes = await get_cg_exchange_volume(exchange, last_btc)
                    print(volumes)
                    await historical_crud.store_gecko_data(session=session, data=volumes)
                except Exception as e:
                    lg.error(e)

        lg.info(exchanges)


        # await historical_crud.save_five_min_exchange_volume(session=session)

async def get_cg_exchange_volume(exchange: dict, btc_rate: float):
    url = f"https://api.coingecko.com/api/v3/exchanges/{exchange['cg_identifier']}/volume_chart?days=30"
    result = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                for item in data:
                    item[0] = int(item[0] // 1000)
                    diff = item[0] % 3600
                    item[0] -= diff
                    result.append({
                        "exchange_id": exchange['id'],
                        "volume_usd": float(item[1]) * float(btc_rate),
                        "timestamp": item[0],
                    })

    return result

if __name__ == '__main__':
    asyncio.run(main())

