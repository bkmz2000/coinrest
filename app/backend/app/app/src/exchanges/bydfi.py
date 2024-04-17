import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class bydfi(BaseExchange):
    """
        docs: https://bydficryptoexchange.github.io/apidoc/docs/zh/futures/spot-api.html
    """
    def __init__(self):
        self.id = 'bydfi'
        self.cg_id = "bydfi"
        self.full_name = "BYDFi"
        self.base_url = "https://bydfi.com/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'b2b/rank/all')
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
                    data = await resp.json(content_type="text/plain")
                else:
                    raise Exception(resp)
        return data

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get('data', {})
        for symbol, prop in tickers.items():
            symbol = self._convert_symbol_to_ccxt(symbol)
            normalized_data[symbol] = {
                "last": float(prop.get("last_price", 0)),
                "baseVolume": float(prop.get("base_volume", 0)),
                "quoteVolume": float(prop.get("quote_volume", 0)),
            }
        return normalized_data

    async def load_markets(self):
        return # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
