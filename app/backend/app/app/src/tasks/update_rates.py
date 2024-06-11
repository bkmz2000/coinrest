import asyncio
import os
from datetime import datetime
from loguru import logger as lg

import aiohttp
from src.lib.quotes import quotes
from src.lib import utils
from src.db.crud import update_quote_mapper, update_fiat_currency_rates
from src.db.connection import AsyncSessionFactory

async def _get_data(url):
    params = {
        "apikey": os.environ.get("FMG_API_KEY")
    }
    data = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
    return data


async def get_rates_from_fmg() -> list[utils.QuoteRate]:
    """Get actual currency rates"""
    lg.info("Fetching quotes")
    rates = []
    for quote in quotes:
        url = f"https://financialmodelingprep.com/api/v4/crypto/last/{quote}USD"
        data = await _get_data(url)
        if not data:
            continue
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

async def get_rates_for_VNST() -> utils.QuoteRate:
    """Вычисляем курс монеты ВНСТ через эфир, потому что это всратая монета и её ни где не найти("""
    url = "https://nami.exchange/api/v1.0/market/summaries"
    eth_usd = 0
    eth_vnst = 1
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                    tickers = data.get('data', [])
                    for ticker in tickers:
                        if ticker.get('symbol') == "ETHUSDT":
                            eth_usd = ticker.get('last_price')
                        if ticker.get('symbol') == "ETHVNST":
                            eth_vnst = ticker.get('last_price')
        vnst_rate = eth_usd/eth_vnst
    except Exception as e:
        lg.error(e)
        vnst_rate = 0
    rate = utils.QuoteRate(currency='VNST', rate=vnst_rate, update_at=datetime.now())
    return rate


async def get_currency_rates() -> list[utils.FiatRate]:
    url = "https://financialmodelingprep.com/api/v3/stock/real-time-price"
    data = await _get_data(url)
    rates = []
    stock_list = data.get("stockList", [])
    for stock in stock_list:
        if stock.get('symbol', '').endswith("USD"):
            rates.append(
                utils.FiatRate(
                    currency=stock['symbol'][:-3],
                    rate=1 / stock['price'],
                    updated_at=datetime.now(),
                )
            )
    return rates

async def main() -> None:
    fiat_rates = await get_currency_rates()
    quote_rates = await get_rates_from_fmg()
    vnst_rate = await get_rates_for_VNST()
    quote_rates.append(vnst_rate)
    async with AsyncSessionFactory() as session:
        await update_quote_mapper(session=session, rates=quote_rates)
        await update_fiat_currency_rates(session=session, rates=fiat_rates)
    lg.info("Currency rates updated")

if __name__ == "__main__":
    asyncio.run(main())