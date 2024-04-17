import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class coinsbit(BaseExchange):
    """
        docs: https://coinsbitwsapi.notion.site/API-COINSBIT-WS-API-COINSBIT-cf1044cff30646d49a0bab0e28f27a87
    """
    def __init__(self):
        self.id = 'coinsbit'
        self.cg_id = "coinsbit"
        self.full_name = "Coinsbit"
        self.base_url = "https://coinsbit.io/api/v1/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'public/tickers')
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
        tickers = data.get('result', {})
        for symbol, prop in tickers.items():
            ticker = prop['ticker']
            symbol = self._convert_symbol_to_ccxt(symbol)
            normalized_data[symbol] = {
                "last": float(ticker.get("last", 0)),
                "baseVolume": float(ticker.get("vol", 0)),
                "quoteVolume": 0
            }
        return normalized_data

    async def load_markets(self):
        return # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
