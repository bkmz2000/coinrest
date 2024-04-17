import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class coinw(BaseExchange):
    """
        docs: https://www.coinw.com/front/API
    """
    def __init__(self):
        self.id = 'coinw'
        self.cg_id = "coinw"
        self.full_name = "CoinW"
        self.base_url = "https://api.coinw.com/api/v1/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'public?command=returnTicker')
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
        tickers = data.get("data", {})
        for raw_symbol, row in tickers.items():
            symbol = self._convert_symbol_to_ccxt(raw_symbol)
            normalized_data[symbol] = {
                "last": float(row.get("last", 0)),
                "baseVolume": 0,
                "quoteVolume": float(row.get("baseVolume", 0))  # base -> quote, coinw wrong volume type
            }
        return normalized_data

    async def load_markets(self):
        return # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
