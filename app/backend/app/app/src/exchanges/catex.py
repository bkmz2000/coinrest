import asyncio

import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange


class catex(BaseExchange):
    """
        docs: https://github.com/catex/catex_exchange_api/wiki/Acquire-all-trading-pairs-volume-and-price-by-list
    """
    def __init__(self):
        self.id = 'catex'
        self.cg_id = "catex"
        self.full_name = "Catex"
        self.base_url = "https://www.catex.io/"
        self.markets = {}

    async def fetch_data(self, url: str):
        """
        :param url: URL to fetch the data from exchange
        :return: raw data
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json(content_type='text/plain')
                else:
                    raise Exception(resp)
        return data

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'api/token/list')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get('data', {})
        for ticker in tickers:
            symbol = ticker.get("pair")
            normalized_data[symbol] = {
                "last": float(ticker.get("priceByBaseCurrency", 0)),
                "baseVolume": float(ticker.get("volume24HoursByCurrency", 0)),
                "quoteVolume": float(ticker.get("volume24HoursByBaseCurrency", 0)),
            }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
