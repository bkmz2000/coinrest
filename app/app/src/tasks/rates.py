import asyncio
import os
from datetime import datetime
from loguru import logger as lg

import aiohttp
from src.lib.quotes import quotes
from src.lib import utils
from src.db.crud import update_quote_mapper
from src.db.connection import AsyncSessionFactory

async def get_rates_from_fmg() -> list[utils.QuoteRate]:
    """Get actual currency rates"""
    lg.info("Fetching quotes")
    rates = []
    for quote in quotes:
        url = f"https://financialmodelingprep.com/api/v4/crypto/last/{quote}USD"
        params = {
            "apikey": os.environ.get("FMG_API_KEY")
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                    currency = data.get("symbol")[:-3]
                    rate = data.get("price")
                    stamp = data.get("timestamp")
                    if stamp:
                        stamp = int(stamp) // 1000
                        update = datetime.utcfromtimestamp(stamp)
                    else:
                        update = datetime.now()
                    rate = utils.QuoteRate(currency=currency, rate=rate, update_at=update)
                    rates.append(rate)
    return rates


async def main() -> None:
    rates = await get_rates_from_fmg()
    async with AsyncSessionFactory() as session:
        await update_quote_mapper(session=session, rates=rates)
    lg.info("Currency rates updated")

if __name__ == "__main__":
    asyncio.run(main())