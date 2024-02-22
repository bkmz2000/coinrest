import aiohttp
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


class cointrpro:
    """
        docs: https://cointr-ex.github.io/openapis/spot.html#market-snapshot
    """
    def __init__(self):
        self.id = 'cointrpro'
        self.base_url = "https://api.cointr.pro/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'v1/spot/market/tickers')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str | list[str]) -> str:
        if isinstance(symbols, str):
            return self.markets.get(symbols.upper())
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
        tickers = data.get("data", [])
        for row in tickers:
            symbol = self._convert_symbol_to_ccxt(row.get('instId'))
            normalized_data[symbol] = {
                "last": float(row.get('lastPx', 0)),
                "baseVolume": float(row.get('vol24h', 0)),
                "quoteVolume": float(row.get('volCcy24h', 0))
            }
        return normalized_data

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + 'v1/spot/public/instruments')
        symbols = data.get("data", [])
        for symbol in symbols:
            base = symbol["baseCcy"]
            quote = symbol["quoteCcy"]
            if base and quote:
                self.markets[base + quote] = base + "/" + quote

    async def close(self):
        pass
