import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class difx(BaseExchange):
    """
        docs: https://api-docs.difx.com/#d7c5576d-04c4-47ce-b739-7562d98d7abc
    """
    def __init__(self):
        self.id = 'difx'
        self.cg_id = "difx"
        self.full_name = "DIFX"
        self.base_url = "https://api-v2.difx.com/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'open/api/v1/ticker')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str | list[str]) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
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
        for symbol, prop in data.items():
            symbol = self._convert_symbol_to_ccxt(symbol)
            normalized_data[symbol] = {
                "last": float(prop.get("last_price", 0)),
                "baseVolume": float(prop.get("base_volume", 0)),
                "quoteVolume": float(prop.get("quote_volume", 0))
            }
        return normalized_data

    async def load_markets(self):
        return # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
