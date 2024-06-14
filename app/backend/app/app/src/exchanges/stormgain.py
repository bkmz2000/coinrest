import asyncio

from src.exchanges.base import BaseExchange
from aiohttp_proxy import ProxyConnector, ProxyType
from src.deps.proxy import ProxyManager
import aiohttp



class stormgain(BaseExchange):
    """
        https://app.stormgain.com/docs/crypto/en/stormgain-api-coingecko-endpoint.pdf
    """
    def __init__(self):
        self.id = "stormgain"
        self.cg_id = "stormgain"
        self.full_name = "Stormgain"
        self.base_url = "https://public-api.stormgain.com"
        self.markets = {}

    async def fetch_data(self, url: str):
        proxy = ProxyManager().get_proxy()

        connector = ProxyConnector(
            proxy_type=ProxyType.HTTP,
            host=proxy.host,
            port=proxy.port,
            username=proxy.username,
            password=proxy.password,
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/api/v1/cg/spot/tickers")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/api/v1/cg/spot/pairs")
        symbols = data
        for symbol in symbols:
            base = symbol["base"]
            quote = symbol["target"]
            if base and quote:
                self.markets[base + "/" + quote] = base + quote

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for result in data:
            symbol = self._convert_symbol_to_ccxt(result.get("ticker_id"))
            normalized_data[symbol] = {
                "last": float(result.get("last_price", 0)),
                "baseVolume": float(result.get("base_volume", 0)),
                "quoteVolume": float(result.get("target_volume", 0)),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
