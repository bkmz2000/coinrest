import aiohttp
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


class tidex:
    """
        docs: https://tidex.gitbook.io/api/trading/public/list-of-public-tickers
    """
    def __init__(self):
        self.id = 'tidex'
        self.base_url = "https://api.tidex.com/api/v1/"
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
            symbol = self._convert_symbol_to_ccxt(symbol)
            ticker = prop.get('ticker', {})
            normalized_data[symbol] = {
                "last": float(ticker.get("last", 0)),
                "baseVolume": 0,
                "quoteVolume": float(ticker.get("deal", 0))
            }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass
