import asyncio
import os
from dataclasses import dataclass
from src.db.connection import AsyncSessionFactory
from src.lib.schema import StrapiMarket
from src.db.cruds.crud_exchange import ExchangeCRUD

import aiohttp

from loguru import logger as lg

# base_url = os.environ.get("STRAPI_URL", 'http://0.0.0.0:1337')
base_url = os.environ.get("STRAPI_URL", 'https://devapp.hodler.sh/strapi')


async def get_strapi_exchanges() -> list:
    """
    Get list with strapi exchanges raw data
    """
    async with aiohttp.ClientSession() as session:
        url = base_url + "/api/exchanges?populate=*&pagination[limit]=500&publicationState=preview"
        async with session.get(url) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                return data['data']


def get_exchanges_data(exchanges: list) -> list[StrapiMarket]:
    """
    Parse raw data from strapi
    """
    to_update = []
    for ex in exchanges:
        attrs = ex.get('attributes', {})
        url = ''
        if attrs:
            img = attrs.get('logo', {}).get('data')
            if img:
                url = base_url + img[0].get('attributes', {}).get('url')

        to_update.append(
            StrapiMarket(
                ccxt_name=attrs.get('name'),
                cg_identifier=attrs.get('cg_identifier'),
                full_name=attrs.get('full_name'),
                trust_score=attrs.get('trust_score'),
                centralized=attrs.get('centralized'),
                logo=url,
                is_active=attrs.get('is_active'),
            )
        )
    return to_update


async def main():
    """
        Synchronize strapi exchanges data with local DB (trust_score, image path, is_active)
    """
    lg.info("Start synchronizing with strapi")
    exchanges = await get_strapi_exchanges()
    if exchanges:
        to_update = get_exchanges_data(exchanges)
        async with AsyncSessionFactory() as session:
            crud = ExchangeCRUD()
            await crud.update_many(session, to_update)
    lg.info("Synchronized successfully")

if __name__ == '__main__':
    asyncio.run(main())