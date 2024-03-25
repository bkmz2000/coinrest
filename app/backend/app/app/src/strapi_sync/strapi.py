import asyncio
import os

import aiohttp

from loguru import logger as lg
from src.lib.schema import UpdateEventTo

# base_url = os.environ.get("STRAPI_URL", 'http://0.0.0.0:1337')
base_url = os.environ.get("STRAPI_URL", 'http://192.168.0.103:1337')
token = os.environ.get("STRAPI_TOKEN")

headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}

async def get_strapi_exchange_id(ccxt_name) -> int:
    async with aiohttp.ClientSession() as session:
        url = base_url + f'/api/exchanges?filters[name][$eq]={ccxt_name}&publicationState=preview'
        async with session.get(url, headers=headers) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                strapi_id = data['data'][0]["id"]

                return strapi_id
            else:
                raise Exception(resp)

async def update(strapi_id: int, data: dict) -> None:
    async with aiohttp.ClientSession() as session:
        url = base_url + f'/api/exchanges/{strapi_id}'
        payload = {
            "data": data
        }
        await session.put(url, json=payload, headers=headers)


async def update_strapi_state(exchange: str, data: UpdateEventTo):
    try:
        strapi_id = await get_strapi_exchange_id(exchange)
        await update(strapi_id, data.model_dump())
    except Exception as e:
        lg.error(f"Failed strapi update {e}")



async def main():
    strapi_id = await get_strapi_exchange_id("bequant")
    data = {
        "ticker_num": 4
    }
    await update(strapi_id, data)

if __name__ == "__main__":
    asyncio.run(main())