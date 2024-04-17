import asyncio
import os
from dataclasses import asdict

import aiohttp

from loguru import logger as lg
from src.lib.utils import UpdateEventTo, CreateExchange

# base_url = os.environ.get("STRAPI_URL", 'http://0.0.0.0:1337')
base_url = os.environ.get("STRAPI_URL")
token = os.environ.get("STRAPI_TOKEN")

headers = {"Authorization": f"bearer {token}", "Content-Type": "application/json"}


async def get_strapi_exchange_id(ccxt_name) -> int:
    async with aiohttp.ClientSession() as session:
        url = base_url + f'/api/exchanges?filters[name][$eq]={ccxt_name}&publicationState=preview'
        async with session.get(url, headers=headers) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                data = data['data']
                if data:
                    strapi_id = data[0]["id"]
                    return strapi_id
            else:
                raise Exception(resp)

async def update(strapi_id: int, data: dict) -> None:
    async with aiohttp.ClientSession() as session:
        url = base_url + f'/api/exchanges/{strapi_id}'
        payload = {
            "data": data
        }
        async with session.put(url, json=payload, headers=headers) as resp:
            if not resp or resp.status != 200:
                lg.warning(f"Cant update strapi {resp}")

async def create(data: CreateExchange):
    async with aiohttp.ClientSession() as session:
        url = base_url + f'/api/exchanges'
        payload = {
            "data": {
                "name": data.ccxt_name,
                "full_name": data.full_name,
                "cg_identifier": data.cg_identifier
            }
        }

        async with session.post(url, json=payload, headers=headers) as resp:
            if not resp or resp.status != 200:
                lg.warning(f"Cant create strapi exchange {resp}")


async def update_strapi_state(exchange: str, data: UpdateEventTo):
    try:
        strapi_id = await get_strapi_exchange_id(exchange)
        await update(strapi_id, data.model_dump())
    except Exception as e:
        lg.error(f"Failed strapi update {e}")


async def create_strapi_exchange(data: CreateExchange):
    try:
        exchange_exists = await get_strapi_exchange_id(data.ccxt_name)
        if exchange_exists:
            return
        await create(data)
        lg.info(f"New exchange {data.ccxt_name} created in strapi")
    except Exception as e:
        lg.error(f"Failed strapi exchange create {e}")


async def main():
    strapi_id = await get_strapi_exchange_id("bequant")
    data = {
        "ticker_num": 4
    }
    await update(strapi_id, data)

if __name__ == "__main__":
    asyncio.run(main())