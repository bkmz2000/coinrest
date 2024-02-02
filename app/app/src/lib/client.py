import asyncio
import os

import aiohttp
from loguru import logger as lg


async def get_coingecko_ids_from_hodler() -> set:
    """
        Получаем все cg_id которые есть у ходлера
    """
    coins = await fetch_data_from_hodler()
    if not coins:
        return set()
    cg_ids = {coin["cgid"] for coin in coins}
    lg.info(f"Fetched coingecko ids: {len(cg_ids)}")
    return cg_ids


async def fetch_data_from_hodler() -> list:
    """
        Получаем последние данные по монетам с ходлера
    """
    lg.info("Fetching data from hodler")
    coins = []
    headers = {
        "Accept": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        # for offset in range(0, 1000, 1000):
        for offset in range(0, 14000, 1000):
            async with session.get(f"https://api2.hodler.sh/coins?batch_size=1000&offset={offset}",
                                   headers=headers) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                    coins.extend(data["coins"])
                else:
                    lg.error(f"Unable fetch data from hodler: {resp}")
            await asyncio.sleep(0.5)
    return coins


async def fetch_data_from_fmg() -> dict[str, float]:
    """Get actual currency rates"""
    url = "https://financialmodelingprep.com/api/v3/stock/real-time-price"
    params = {
        "apikey": os.environ.get("FMG_API_KEY")
    }
    rates = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                stock_list = data["stockList"]
                for stock in stock_list:
                    if stock.get('symbol', '').endswith("USD"):
                        rates[stock['symbol'][:-3]] = stock['price']
            else:
                lg.error(f"{resp}")
    return rates


if __name__ == '__main__':
    # asyncio.run(get_coingecko_ids_from_hodler())
    asyncio.run(fetch_data_from_fmg())
