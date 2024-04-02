import asyncio
from src.db.cruds.crud_actual_coingecko import ActualCoingeckoCRUD
from src.db.connection import AsyncSessionFactory
from src.lib import utils
from loguru import logger as lg
import aiohttp

url = "https://api.coingecko.com/api/v3/coins/list"


async def fetch_coin_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                return data


def parse_data(data: list) -> list[utils.ActualCoinIn]:
    result = []
    for coin in data:
        result.append(
            utils.ActualCoinIn(
                cg_id=coin["id"]
            )
        )
    return result


async def main():
    lg.info("Fetching actual coins list from coingecko")
    data = await fetch_coin_data()
    if not data:
        lg.warning("Actual coins list from coingecko not updated")
        return
    gecko_ids = parse_data(data)
    crud = ActualCoingeckoCRUD()

    async with AsyncSessionFactory() as session:
        await crud.store_actual_geckos(session=session, coins=gecko_ids)
    lg.info("Actual coins list was updated successfully")

if __name__ == "__main__":
    asyncio.run(main())
