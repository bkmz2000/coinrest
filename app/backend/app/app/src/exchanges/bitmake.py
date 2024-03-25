import aiohttp
from loguru import logger as lg


class bitmake:
    """
        docs: https://docs.bitmake.com/#get-summary
    """
    def __init__(self):
        self.id = 'bitmake'
        self.base_url = "https://api.bitmake.com/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 't/v1/quote/summary')
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

    def normalize_data(self, data: list) -> dict:
        normalized_data = {}
        for ticker in data:
            print(ticker)
            symbol = self._convert_symbol_to_ccxt(ticker.get("symbol", ''))
            normalized_data[symbol] = {
                "last": float(ticker.get("lastSymbolPrice", 0)),
                "baseVolume": float(ticker.get("baseVolume24", 0)),
                "quoteVolume": float(ticker.get("quoteVolume24", 0))
            }
        return normalized_data

    async def load_markets(self):
        return # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
