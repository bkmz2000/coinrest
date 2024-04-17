import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class fastex(BaseExchange):
    """
        docs: https://exchange.fastex.com/api/documentation#tag/public/paths/~1stats~1marketdepth/get
    """
    def __init__(self):
        self.id = 'fastex'
        self.cg_id = "fastex"
        self.full_name = "Fastex"
        self.base_url = "http://exchange.fastex.com/api/v1/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + "stats/marketdepthfull")
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str | list[str]) -> str:
        if isinstance(symbols, str):
            return symbols.upper()
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    async def fetch_data(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get('response', {}).get('entities', [])
        for row in tickers:
            symbol = self._convert_symbol_to_ccxt(row.get('pair_name'))
            normalized_data[symbol] = {
                "last": float(row.get('last_price', 0)),
                "baseVolume": float(row.get('vol', 0)),
                "quoteVolume": 0
            }
        return normalized_data

    async def load_markets(self):
        pass

    async def close(self):
        pass
