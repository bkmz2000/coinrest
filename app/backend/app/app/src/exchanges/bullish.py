import aiohttp
# from aiohttp_proxy import ProxyConnector, ProxyType
from src.exchanges.base import BaseExchange
from loguru import logger as lg


class bullish(BaseExchange):
    """
        docs: https://api.exchange.bullish.com/docs/api/rest/trading-api/v2/#get-/markets/-symbol-/tick
    """
    def __init__(self):
        self.id = 'bullish'
        self.cg_id = "bullish_com"
        self.full_name = "Bullish"
        self.base_url = "https://api.exchange.bullish.com/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()

        result = {}
        for symbol in self.markets:
            url = self.base_url + 'trading-api/v1/markets/' + symbol + '/tick'
            data = await self.fetch_data(url)
            if data:
                result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "trading-api/v1/markets/")
        for symbol in data:
            base = symbol["baseSymbol"]
            quote = symbol["quoteSymbol"]
            if base and quote:
                self.markets[base+quote] = base + "/" + quote

    async def fetch_data(self, url: str):
        # connector = ProxyConnector(
        #     proxy_type=ProxyType.SOCKS5,
        #     host='127.0.0.1',
        #     port=9999,
        #     rdns=True
        # )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    data = {}
        return data

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        symbol = self._convert_symbol_to_ccxt(data.get("symbol"))
        normalized_data[symbol] = {
            "last": float(data.get("last", 0)),
            "baseVolume": float(data.get("baseVolume", 0)),
            "quoteVolume": float(data.get("quoteVolume", 0))
        }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            return self.markets.get(symbols)
        raise TypeError(f"{symbols} invalid type")

    async def close(self):
        pass