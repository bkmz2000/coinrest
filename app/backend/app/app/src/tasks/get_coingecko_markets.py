import asyncio
import os

import aiohttp
from loguru import logger as lg
from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_actual_coingecko import ActualCoingeckoCRUD
from src.db.cruds.crud_ticker import TickerCRUD
from src.db.cruds.crud_last import LastCRUD
from src.lib.schema import CoinOutput


COINGECKO_TOKEN = os.environ.get("COINGECKO_TOKEN")
API_KEY = f"x_cg_pro_api_key={COINGECKO_TOKEN}"


async def main():
    gecko_crud, ticker_crud, last_crud = ActualCoingeckoCRUD(), TickerCRUD(), LastCRUD()
    coins_to_request = []
    async with AsyncSessionFactory() as session:
        coingecko_ids = await gecko_crud.get_actual_geckos(session=session)
        exchanges_coins = await ticker_crud.get_actual_coins(session=session)
        exchanges_coins = set(exchanges_coins)

        lg.info(f"Actual coins from exchanges: {len(exchanges_coins)}")
        for coin in coingecko_ids:
            if coin not in exchanges_coins:
                coins_to_request.append(coin)

        lg.info(f"To fetch from coingecko: {len(coins_to_request)}")
        for i in range(0, len(coins_to_request), 250):
            coins = coins_to_request[i: i + 250]
            coins = ','.join(coins)
            data = await fetch_coingecko_markets(coins)
            if data:
                await last_crud.save_last(session=session, coins=data)


async def fetch_coingecko_markets(coins: str) -> list[CoinOutput]:
    url = f"https://pro-api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd,btc&include_24hr_vol=true&{API_KEY}"
    result = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                for coin_id, props in data.items():
                    result.append(CoinOutput(
                        cg_id=coin_id,
                        price_usd=props.get("usd", 0),
                        volume_usd=props.get("usd_24h_vol", 0),
                        price_btc=props.get("btc", 0),
                        volume_btc=props.get("btc_24h_vol", 0)
                    ))
                return result
            else:
                lg.error(f"Unable to fetch data from coingecko {resp}, {resp.json()}")

if __name__ == "__main__":
    asyncio.run(main())