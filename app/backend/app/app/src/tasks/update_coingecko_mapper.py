import asyncio
import aiohttp

from loguru import logger as lg
from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_exchange import ExchangeCRUD


async def main():
    lg.info("New mapper started")
    async with AsyncSessionFactory() as session:
        ex = ExchangeCRUD()
        ids = await ex.get_exchanges(session=session)
        l = len(ids)
        for i, exchange in enumerate(ids):
            lg.debug(f"{i}/{l}: {exchange.cg_identifier}")
            mapped = {}
            try:
                await get_exchange_tickers(exchange.cg_identifier, mapped)
                if mapped:
                    await ex.save_mappings(session=session, exchange_id=exchange.id, mapped=mapped)
            except Exception as e:
                lg.error(f"{exchange} {e}")
    lg.info("New mapper updated")


async def get_exchange_tickers(exchange: str, mapped: dict):
    """
        Get all exchange ticker mappings
    """
    page = 1
    while True:
        lg.debug(f"{exchange}, page={page}")
        url = f"https://api.coingecko.com/api/v3/exchanges/{exchange}/tickers?page={page}"
        data = await _fetch_data(url)
        tickers = data.get('tickers')
        if not tickers:
            return
        _parse_tickers(tickers, mapped)
        page += 1


def _parse_tickers(tickers: list, mapped: dict):
    if not tickers:
        return
    for ticker in tickers:
        base = ticker.get('base')
        base_mapped = ticker.get('coin_id')
        if base and base_mapped and base not in mapped:
            mapped[base] = base_mapped

        target = ticker.get('target')
        target_mapped = ticker.get('target_coin_id')
        if target and target_mapped and target not in mapped:
            mapped[target] = target_mapped


async def _fetch_data(url: str):
    await asyncio.sleep(15)  # delay, not to be banned by coingecko
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
            else:
                data = {}
                lg.error(resp)
    return data

if __name__ == '__main__':
    asyncio.run(main())